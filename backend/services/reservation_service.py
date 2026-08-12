from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.core.exceptions import DomainError
from backend.models.entities import Book, BookCopy, Borrowing, BorrowingStatus, CopyStatus, Reservation, ReservationStatus, User, UserStatus
from backend.services.audit_service import audit
from backend.services.notification_service import notify_user
from backend.services.policy_service import reservation_hold_days


def expire_reservations(db: Session) -> int:
    """Expire elapsed pickup holds and advance the queue transactionally."""
    now = datetime.now(timezone.utc)
    expired = list(db.scalars(select(Reservation).where(
        Reservation.status == ReservationStatus.READY,
        Reservation.expires_at.is_not(None),
        Reservation.expires_at <= now,
    )))
    for reservation in expired:
        reservation.status = ReservationStatus.EXPIRED
        copy = db.scalar(select(BookCopy).where(
            BookCopy.book_id == reservation.book_id,
            BookCopy.status == CopyStatus.RESERVED,
            ~BookCopy.borrowings.any(Borrowing.status.in_([BorrowingStatus.ACTIVE, BorrowingStatus.OVERDUE])),
        ).with_for_update())
        next_in_line = db.scalars(select(Reservation).where(
            Reservation.book_id == reservation.book_id,
            Reservation.status == ReservationStatus.ACTIVE,
        ).order_by(Reservation.reserved_at).with_for_update()).first()
        if copy and next_in_line:
            next_in_line.status = ReservationStatus.READY
            next_in_line.expires_at = now + __import__("datetime").timedelta(days=reservation_hold_days(db))
            notify_user(db, next_in_line.user_id, "RESERVATION_AVAILABLE", f"{next_in_line.book.title} is ready for pickup until {next_in_line.expires_at.date().isoformat()}.", subject="LIBRAI: Reserved book ready")
        elif copy:
            copy.status = CopyStatus.ARCHIVED if copy.book.is_archived else CopyStatus.AVAILABLE
        audit(db,"RESERVATION_EXPIRED","reservation",reservation.id,actor_type="SYSTEM")
    if expired:
        db.commit()
    return len(expired)


def create_reservation(db: Session, user_id: int, book_id: int) -> tuple[Reservation, int]:
    expire_reservations(db)
    user, book = db.get(User, user_id), db.get(Book, book_id)
    if not user or user.status != UserStatus.ACTIVE: raise DomainError("USER_NOT_ELIGIBLE", "An active library account is required.")
    if not book or book.is_archived: raise DomainError("BOOK_NOT_FOUND", "Book not found.", 404)
    if not db.scalar(select(BookCopy).where(BookCopy.book_id == book_id, BookCopy.status != CopyStatus.ARCHIVED)):
        raise DomainError("BOOK_HAS_NO_COPIES", "This title has no physical copies and cannot be reserved.")
    if db.scalar(select(BookCopy).where(BookCopy.book_id == book_id, BookCopy.status == CopyStatus.AVAILABLE)):
        raise DomainError("BOOK_AVAILABLE", "This title is available and does not need a reservation.")
    existing = db.scalar(select(Reservation).where(Reservation.user_id == user_id, Reservation.book_id == book_id, Reservation.status.in_([ReservationStatus.ACTIVE, ReservationStatus.READY])))
    if existing: raise DomainError("DUPLICATE_RESERVATION", "The user already has an active reservation for this title.")
    reservation = Reservation(user_id=user_id, book_id=book_id, status=ReservationStatus.ACTIVE); db.add(reservation); db.flush()
    position = db.scalar(select(func.count(Reservation.id)).where(Reservation.book_id == book_id, Reservation.status == ReservationStatus.ACTIVE, Reservation.reserved_at <= reservation.reserved_at)) or 1
    notify_user(db, user_id, "RESERVATION_CREATED", f"Reservation created for {book.title}; queue position {position}.", subject="LIBRAI: Reservation created"); audit(db,"RESERVATION_CREATED","reservation",reservation.id,actor_type="KIOSK",actor_id=user_id)
    try:
        db.commit(); db.refresh(reservation); return reservation, position
    except IntegrityError as exc:
        db.rollback(); raise DomainError("DUPLICATE_RESERVATION", "The user already has an active reservation for this title.") from exc
