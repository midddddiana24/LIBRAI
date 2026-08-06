from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, joinedload
from backend.core.exceptions import DomainError
from backend.models.entities import BookCopy, Borrowing, BorrowingStatus, CopyStatus, Notification, RenewalHistory, Reservation, ReservationStatus, User, UserStatus
from backend.services.audit_service import audit
from backend.services.policy_service import allow_overdue, borrowing_limit, borrowing_period_days, max_renewals, reservation_hold_days
from backend.services.reservation_service import expire_reservations


def _mark_overdue(db: Session, user_id: int | None = None) -> None:
    now = datetime.now(timezone.utc)
    stmt = select(Borrowing).where(Borrowing.status == BorrowingStatus.ACTIVE, Borrowing.due_at < now)
    if user_id: stmt = stmt.where(Borrowing.user_id == user_id)
    for item in db.scalars(stmt): item.status = BorrowingStatus.OVERDUE


def borrow_book(db: Session, user_id: int, copy_id: int, kiosk_id=None) -> Borrowing:
    expire_reservations(db)
    try:
        with db.begin_nested():
            user = db.get(User, user_id)
            if not user: raise DomainError("USER_NOT_FOUND", "The library user does not exist.", 404)
            if user.status != UserStatus.ACTIVE: raise DomainError("USER_INACTIVE", "This library account is not active.")
            _mark_overdue(db, user_id)
            statuses = [BorrowingStatus.ACTIVE, BorrowingStatus.OVERDUE]
            overdue = db.scalar(select(func.count(Borrowing.id)).where(Borrowing.user_id == user_id, Borrowing.status == BorrowingStatus.OVERDUE)) or 0
            if overdue and not allow_overdue(db): raise DomainError("OVERDUE_RESTRICTION", "Return overdue books before borrowing another item.")
            active = db.scalar(select(func.count(Borrowing.id)).where(Borrowing.user_id == user_id, Borrowing.status.in_(statuses))) or 0
            if active >= borrowing_limit(db): raise DomainError("BORROWING_LIMIT_REACHED", "The user has reached the borrowing limit.")
            copy = db.scalar(select(BookCopy).where(BookCopy.id == copy_id).with_for_update())
            if not copy: raise DomainError("BOOK_COPY_NOT_FOUND", "The physical book copy does not exist.", 404)
            if copy.status != CopyStatus.AVAILABLE: raise DomainError("BOOK_COPY_UNAVAILABLE", "This book copy is not available.")
            duplicate = db.scalar(select(Borrowing).join(BookCopy).where(Borrowing.user_id == user_id, BookCopy.book_id == copy.book_id, Borrowing.status.in_(statuses)))
            if duplicate: raise DomainError("DUPLICATE_ACTIVE_BORROWING", "The user already has an active copy of this title.")
            queue = db.scalars(select(Reservation).where(Reservation.book_id == copy.book_id, Reservation.status.in_([ReservationStatus.ACTIVE, ReservationStatus.READY])).order_by(Reservation.reserved_at).with_for_update()).first()
            if queue and queue.user_id != user_id: raise DomainError("RESERVED_FOR_ANOTHER_USER", "This title is reserved for another user.")
            now = datetime.now(timezone.utc)
            borrowing = Borrowing(user_id=user_id, book_copy_id=copy.id, borrowed_at=now, due_at=now + timedelta(days=borrowing_period_days(db)), status=BorrowingStatus.ACTIVE, kiosk_id=kiosk_id, created_by="KIOSK")
            claimed = db.execute(update(BookCopy).where(BookCopy.id == copy.id, BookCopy.status == CopyStatus.AVAILABLE).values(status=CopyStatus.BORROWED).execution_options(synchronize_session="fetch"))
            if claimed.rowcount != 1: raise DomainError("CONCURRENT_BORROW_CONFLICT", "This copy was borrowed by another transaction. Please scan another copy.")
            db.add(borrowing); db.flush()
            if queue and queue.user_id == user_id: queue.status = ReservationStatus.FULFILLED
            db.add(Notification(user_id=user_id, type="BORROW_SUCCESS", message=f"Borrowed {copy.book.title}; due {borrowing.due_at.date().isoformat()}."))
            audit(db, "BORROW_PERFORMED", "borrowing", borrowing.id, actor_type="KIOSK", actor_id=kiosk_id, details={"user_id": user_id, "copy_id": copy.id})
        db.commit(); db.refresh(borrowing); return borrowing
    except (IntegrityError, OperationalError) as exc:
        db.rollback(); raise DomainError("CONCURRENT_BORROW_CONFLICT", "This copy was borrowed by another transaction. Please scan another copy.") from exc
    except DomainError:
        db.rollback(); raise


def return_book(db: Session, borrowing_id: int) -> tuple[Borrowing, str]:
    expire_reservations(db)
    try:
        with db.begin_nested():
            borrowing = db.scalar(select(Borrowing).options(joinedload(Borrowing.book_copy).joinedload(BookCopy.book)).where(Borrowing.id == borrowing_id).with_for_update())
            if not borrowing: raise DomainError("BORROWING_NOT_FOUND", "No borrowing transaction was found.", 404)
            if borrowing.status not in [BorrowingStatus.ACTIVE, BorrowingStatus.OVERDUE]: raise DomainError("ALREADY_RETURNED", "This borrowing is no longer active.")
            now = datetime.now(timezone.utc)
            due_at = borrowing.due_at if borrowing.due_at.tzinfo else borrowing.due_at.replace(tzinfo=timezone.utc)
            return_status = "overdue" if now > due_at else "on_time"
            borrowing.returned_at = now; borrowing.status = BorrowingStatus.RETURNED
            copy = borrowing.book_copy
            queue = db.scalars(select(Reservation).where(Reservation.book_id == copy.book_id, Reservation.status == ReservationStatus.ACTIVE).order_by(Reservation.reserved_at).with_for_update()).first()
            if queue:
                copy.status = CopyStatus.RESERVED; queue.status = ReservationStatus.READY; queue.expires_at = now + timedelta(days=reservation_hold_days(db))
                db.add(Notification(user_id=queue.user_id, type="RESERVATION_AVAILABLE", message=f"{copy.book.title} is ready for pickup."))
            else: copy.status = CopyStatus.ARCHIVED if copy.book.is_archived else CopyStatus.AVAILABLE
            db.add(Notification(user_id=borrowing.user_id, type="RETURN_SUCCESS", message=f"Returned {copy.book.title} ({return_status.replace('_',' ')})."))
            audit(db, "RETURN_PERFORMED", "borrowing", borrowing.id, actor_type="KIOSK", details={"copy_id": copy.id, "return_status": return_status})
        db.commit(); return borrowing, return_status
    except DomainError: db.rollback(); raise


def renew_borrowing(db: Session, borrowing_id: int, user_id: int) -> Borrowing:
    """Extend an eligible active loan and preserve an immutable renewal trail."""
    try:
        with db.begin_nested():
            borrowing = db.scalar(
                select(Borrowing)
                .options(joinedload(Borrowing.book_copy).joinedload(BookCopy.book))
                .where(Borrowing.id == borrowing_id)
                .with_for_update()
            )
            if not borrowing or borrowing.user_id != user_id:
                raise DomainError("BORROWING_NOT_FOUND", "This borrowing does not belong to the verified user.", 404)
            now = datetime.now(timezone.utc)
            due_at = borrowing.due_at if borrowing.due_at.tzinfo else borrowing.due_at.replace(tzinfo=timezone.utc)
            if borrowing.status != BorrowingStatus.ACTIVE or due_at < now:
                raise DomainError("RENEWAL_OVERDUE", "Overdue or returned books cannot be renewed.")
            allowed = max_renewals(db)
            if borrowing.renewal_count >= allowed:
                raise DomainError("RENEWAL_LIMIT_REACHED", "This borrowing has reached its renewal limit.")
            waiting = db.scalar(
                select(Reservation).where(
                    Reservation.book_id == borrowing.book_copy.book_id,
                    Reservation.user_id != user_id,
                    Reservation.status.in_([ReservationStatus.ACTIVE, ReservationStatus.READY]),
                )
            )
            if waiting:
                raise DomainError("BOOK_RESERVED", "This title is reserved by another user and cannot be renewed.")
            previous = borrowing.due_at
            borrowing.due_at = due_at + timedelta(days=borrowing_period_days(db))
            borrowing.renewal_count += 1
            db.add(RenewalHistory(borrowing_id=borrowing.id, previous_due_at=previous, new_due_at=borrowing.due_at, actor_type="KIOSK"))
            db.add(Notification(user_id=user_id, type="RENEWAL_SUCCESS", message=f"Renewed {borrowing.book_copy.book.title}; new due date {borrowing.due_at.date().isoformat()}."))
            audit(db, "BORROWING_RENEWED", "borrowing", borrowing.id, actor_type="KIOSK", details={"renewal_count": borrowing.renewal_count, "new_due_at": borrowing.due_at.isoformat()})
        db.commit();db.refresh(borrowing);return borrowing
    except DomainError:
        db.rollback();raise
