from __future__ import annotations

from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from backend.models.entities import BookCopy, Borrowing, EmailDelivery, Notification, User


def is_overdue(loan: Borrowing, now: datetime | None = None) -> bool:
    due = loan.due_at.replace(tzinfo=timezone.utc) if loan.due_at.tzinfo is None else loan.due_at
    return loan.returned_at is None and loan.status in {'ACTIVE', 'OVERDUE'} and due < (now or datetime.now(timezone.utc))


def overdue_message(loan: Borrowing) -> str:
    due = loan.due_at.replace(tzinfo=timezone.utc) if loan.due_at.tzinfo is None else loan.due_at
    local_due = due.astimezone(timezone(timedelta(hours=8))).strftime('%B %d, %Y at %I:%M %p')
    return (f'Your borrowed book "{loan.book_copy.book.title}" (loan #{loan.id}, copy {loan.book_copy.accession_number}) '
            f'was due on {local_due} Philippine time (UTC+08:00) and is overdue. '
            'Please return it to the library. If you have already returned it, contact library staff to check the record.')


def queue_overdue_reminders(db: Session, *, now: datetime | None = None, limit: int = 100) -> int:
    now = now or datetime.now(timezone.utc)
    existing = select(Notification.id).where(Notification.borrowing_id == Borrowing.id, Notification.type == 'OVERDUE_REMINDER').exists()
    loans = db.scalars(select(Borrowing).where(
        Borrowing.status.in_(['ACTIVE', 'OVERDUE']), Borrowing.returned_at.is_(None), Borrowing.due_at < now, ~existing,
    ).options(selectinload(Borrowing.book_copy).selectinload(BookCopy.book)).order_by(Borrowing.due_at, Borrowing.id)
      .limit(limit).with_for_update(of=Borrowing, skip_locked=True)).all()
    for loan in loans:
        message = overdue_message(loan)
        notify_user(db, loan.user_id, 'OVERDUE_REMINDER', message,
                    subject='LIBRAI: Your borrowed book is overdue', email_body=message, borrowing_id=loan.id)
    return len(loans)


def queue_library_id(db: Session, user: User) -> Notification:
    """The worker creates the current QR in memory only after staff approval."""
    message = ("Your library account is approved. Your LIBRAI library ID QR is attached to the email."
               if user.email else "Your library account is approved. Ask library staff for your LIBRAI library ID QR.")
    return notify_user(db, user.id, "LIBRARY_ID", message,
                       subject="Your LIBRAI library ID", email_body=(
                           f"Hello {user.display_name},\n\nYour library account is approved. "
                           "Save the attached library-id.png and scan it at the LIBRAI kiosk when borrowing books.\n\n"
                           "Keep this QR private. It gives access to your library account. "
                           "If it is lost or shared, ask library staff to replace it.\n\nLIBRAI Library"))


def notify_user(db: Session, user_id: int, type_: str, message: str, *, subject: str | None = None, email_body: str | None = None, borrowing_id: int | None = None) -> Notification:
    notification = Notification(user_id=user_id, type=type_, message=message, borrowing_id=borrowing_id)
    db.add(notification)
    db.flush()
    user = db.get(User, user_id)
    if user and user.email:
        db.add(EmailDelivery(
            user_id=user.id,
            notification_id=notification.id,
            recipient=user.email,
            subject=subject or f"LIBRAI: {type_.replace('_', ' ').title()}",
            body=email_body or message,
        ))
    return notification
