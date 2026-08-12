"""Deliver queued notification emails.

Run as a separate process after configuring SMTP_* environment variables.
"""
from __future__ import annotations
import smtplib
from email.message import EmailMessage
from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.models.entities import EmailDelivery, EmailDeliveryStatus
from sqlalchemy import select

def process(limit: int = 25) -> int:
    required = [settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]
    if not all(required):
        raise RuntimeError("SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM are required.")
    with SessionLocal() as db:
        items = list(db.scalars(select(EmailDelivery).where(EmailDelivery.status == EmailDeliveryStatus.PENDING).order_by(EmailDelivery.created_at).limit(limit)))
        if not items:
            return 0
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            for item in items:
                message = EmailMessage()
                message["From"] = settings.smtp_from
                message["To"] = item.recipient
                message["Subject"] = item.subject
                message.set_content(item.body)
                try:
                    server.send_message(message)
                    item.status = EmailDeliveryStatus.SENT
                    item.sent_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                    item.error = None
                except Exception as exc:
                    item.status = EmailDeliveryStatus.FAILED
                    item.error = str(exc)[:1000]
        db.commit()
        return len(items)

if __name__ == "__main__":
    print(f"EMAIL_WORKER_PROCESSED {process()}")
