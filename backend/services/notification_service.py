from __future__ import annotations

from sqlalchemy.orm import Session
from backend.models.entities import EmailDelivery, Notification, User


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
