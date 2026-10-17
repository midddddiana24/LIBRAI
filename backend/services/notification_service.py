from __future__ import annotations

from sqlalchemy.orm import Session
from backend.models.entities import EmailDelivery, Notification, User


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


def notify_user(db: Session, user_id: int, type_: str, message: str, *, subject: str | None = None, email_body: str | None = None) -> Notification:
    notification = Notification(user_id=user_id, type=type_, message=message)
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
