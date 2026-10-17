"""Send committed notification emails. Run one worker; --watch polls the outbox."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formatdate
from io import BytesIO
import smtplib
import ssl
import time

import qrcode
from sqlalchemy import select
from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.models.entities import EmailDelivery, EmailDeliveryStatus, Notification, User
from backend.services import gmail_service


def configured() -> bool:
    if settings.email_transport == "gmail_api":
        try:
            gmail_service.load_credentials(settings.gmail_oauth_file)
            return True
        except ValueError:
            return False
    return all((settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from))


def build_message(db, item: EmailDelivery) -> EmailMessage:
    message = EmailMessage()
    sender = (gmail_service.load_credentials(settings.gmail_oauth_file)["sender"]
              if settings.email_transport == "gmail_api" else settings.smtp_from)
    message["From"] = sender
    message["To"] = item.recipient
    message["Subject"] = item.subject
    message["Date"] = formatdate(localtime=False)
    # Stable across retries; SMTP acceptance is not proof of inbox delivery.
    domain = sender.rsplit("@", 1)[-1].strip("> ")
    message["Message-ID"] = f"<librai-delivery-{item.id}-{item.created_at.strftime('%Y%m%d%H%M%S%f')}@{domain}>"
    message.set_content(item.body)
    user = db.scalar(select(User).where(User.id == item.user_id).with_for_update()) if item.user_id else None
    if not user or not user.email or user.email.casefold() != item.recipient.casefold():
        raise ValueError("Recipient no longer matches the member account. Queue a new email after correcting the address.")
    notification = db.get(Notification, item.notification_id) if item.notification_id else None
    if notification and notification.type == "LIBRARY_ID":
        if user.status != "ACTIVE":
            raise ValueError("Library ID withheld: the account is not active.")
        image = BytesIO()
        qrcode.make(user.qr_token).save(image, format="PNG")
        message.add_attachment(image.getvalue(), maintype="image", subtype="png", filename="library-id.png")
    return message


def process(limit: int = 25, delivery_id: int | None = None) -> int:
    if not configured():
        raise RuntimeError("Configure GMAIL_OAUTH_FILE for gmail_api, or set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD and SMTP_FROM for smtp.")
    if settings.email_transport == "smtp" and settings.smtp_port != 465 and not settings.smtp_use_tls:
        raise RuntimeError("SMTP requires STARTTLS or port 465 with implicit TLS.")
    processed = 0
    for _ in range(limit):
        with SessionLocal() as db:
            # PostgreSQL locks prevent two workers from sending the same row concurrently.
            # shortcut: SQLite requires a single worker; use PostgreSQL for concurrent workers.
            query = select(EmailDelivery).where(EmailDelivery.status == EmailDeliveryStatus.PENDING)
            if delivery_id is not None:
                query = query.where(EmailDelivery.id == delivery_id)
            item = db.scalar(query.order_by(EmailDelivery.created_at, EmailDelivery.id).limit(1).with_for_update(skip_locked=True))
            if item is None:
                break
            try:
                message = build_message(db, item)
                if settings.email_transport == "gmail_api":
                    gmail_service.send_message(message, gmail_service.load_credentials(settings.gmail_oauth_file))
                else:
                    context = ssl.create_default_context()
                    connection = (smtplib.SMTP_SSL(settings.smtp_host, 465, timeout=20, context=context)
                                  if settings.smtp_port == 465 else smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20))
                    with connection as server:
                        if settings.smtp_port != 465:
                            server.starttls(context=context)
                        server.login(settings.smtp_username, settings.smtp_password)
                        refused = server.send_message(message)
                        if refused:
                            raise smtplib.SMTPRecipientsRefused(refused)
                item.status = EmailDeliveryStatus.SENT
                item.sent_at = datetime.now(timezone.utc)
                item.error = None
            except ValueError as exc:
                item.status = EmailDeliveryStatus.FAILED
                item.error = str(exc)
            except Exception as exc:
                item.status = EmailDeliveryStatus.FAILED
                # Do not store raw SMTP responses, credentials or member content.
                item.error = f"{type(exc).__name__}: delivery failed. Check email credentials, network access and sender settings before retrying; check Sent mail if acceptance is uncertain."
            # Commit each result so a later failure does not reset earlier successes.
            # SMTP has no exactly-once guarantee if the process dies after acceptance.
            db.commit()
            processed += 1
    return processed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watch", action="store_true", help="Poll pending emails until stopped.")
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--delivery-id", type=int, help="Send only this pending delivery, for a controlled first test.")
    args = parser.parse_args()
    if args.interval < 5 or not 1 <= args.limit <= 100 or (args.delivery_id is not None and args.delivery_id < 1):
        parser.error("interval must be at least 5 seconds; limit must be 1 to 100")
    while True:
        try:
            print(f"EMAIL_WORKER_PROCESSED {process(args.limit, args.delivery_id)}", flush=True)
        except RuntimeError as exc:
            parser.exit(1, f"{exc}\n")
        if not args.watch:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
