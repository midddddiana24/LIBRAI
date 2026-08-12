from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from backend.core.exceptions import DomainError
from backend.models.entities import Admin, BookCopy, Borrowing, Fine, FineStatus
from backend.services.audit_service import audit
from backend.services.notification_service import notify_user
from backend.services.policy_service import overdue_fine_per_day_cents


def unpaid_fine_total_cents(db: Session, user_id: int) -> int:
    return db.scalar(select(func.coalesce(func.sum(Fine.amount_cents), 0)).where(Fine.user_id == user_id, Fine.status == FineStatus.UNPAID)) or 0


def assess_overdue_fine(db: Session, borrowing: Borrowing, returned_at: datetime | None = None) -> Fine | None:
    if db.scalar(select(Fine).where(Fine.borrowing_id == borrowing.id, Fine.reason == "OVERDUE")):
        return None
    now = returned_at or datetime.now(timezone.utc)
    due_at = borrowing.due_at if borrowing.due_at.tzinfo else borrowing.due_at.replace(tzinfo=timezone.utc)
    if now <= due_at:
        return None
    overdue_days = max(1, (now.date() - due_at.date()).days)
    amount_cents = overdue_days * overdue_fine_per_day_cents(db)
    fine = Fine(user_id=borrowing.user_id, borrowing_id=borrowing.id, amount_cents=amount_cents, reason="OVERDUE")
    db.add(fine)
    db.flush()
    book_title = borrowing.book_copy.book.title if borrowing.book_copy and borrowing.book_copy.book else "borrowed item"
    notify_user(
        db,
        borrowing.user_id,
        "FINE_ASSESSED",
        f"An overdue fine of PHP {amount_cents / 100:.2f} was assessed for {book_title}.",
        subject="LIBRAI: Overdue fine assessed",
    )
    audit(db, "FINE_ASSESSED", "fine", fine.id, actor_type="SYSTEM", details={"borrowing_id": borrowing.id, "amount_cents": amount_cents, "overdue_days": overdue_days})
    return fine


def fine_dict(fine: Fine) -> dict:
    borrowing = fine.borrowing
    title = borrowing.book_copy.book.title if borrowing and borrowing.book_copy and borrowing.book_copy.book else None
    return {
        "id": fine.id,
        "user_id": fine.user_id,
        "borrowing_id": fine.borrowing_id,
        "book_title": title,
        "amount_cents": fine.amount_cents,
        "amount": round(fine.amount_cents / 100, 2),
        "reason": fine.reason,
        "status": fine.status.lower(),
        "assessed_at": fine.assessed_at,
        "paid_at": fine.paid_at,
        "note": fine.note,
    }


def mark_fine_paid(db: Session, fine_id: int, admin: Admin, note: str | None = None) -> Fine:
    fine = db.scalar(
        select(Fine)
        .options(joinedload(Fine.borrowing).joinedload(Borrowing.book_copy).joinedload(BookCopy.book))
        .where(Fine.id == fine_id)
    )
    if not fine:
        raise DomainError("FINE_NOT_FOUND", "Fine not found.", 404)
    if fine.status != FineStatus.UNPAID:
        raise DomainError("FINE_ALREADY_CLOSED", "Only unpaid fines can be marked as paid.")
    fine.status = FineStatus.PAID
    fine.paid_at = datetime.now(timezone.utc)
    fine.note = note
    notify_user(db, fine.user_id, "FINE_PAID", f"Your fine of PHP {fine.amount_cents / 100:.2f} has been marked paid.", subject="LIBRAI: Fine paid")
    audit(db, "FINE_PAID", "fine", fine.id, admin=admin, details={"amount_cents": fine.amount_cents})
    db.commit()
    db.refresh(fine)
    return fine
