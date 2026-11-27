from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from backend.core.config import settings
from backend.models.entities import Borrowing, EmailDelivery, Notification, User
from backend.services.notification_service import queue_overdue_reminders
from backend.services import email_dispatch
from backend.scripts import email_worker
from backend.tests.test_email_delivery import smtp  # shared fake transport; no real email


def add_loan(db, copy=1, *, due=None, status='ACTIVE', returned_at=None):
    loan = Borrowing(user_id=1, book_copy_id=copy, due_at=due or datetime.now(timezone.utc)-timedelta(days=1), status=status, returned_at=returned_at)
    db.add(loan)
    db.flush()
    return loan


def test_overdue_reminders_are_once_per_loan_across_sessions(db_factory):
    with db_factory() as db:
        add_loan(db)
        add_loan(db, 2, status='OVERDUE')
        assert queue_overdue_reminders(db, limit=1) == 1
        db.commit()
    with db_factory() as db:
        assert queue_overdue_reminders(db) == 1
        db.commit()
    with db_factory() as db:
        assert queue_overdue_reminders(db) == 0
        notices = db.scalars(select(Notification)).all()
        assert len(notices) == 2 and len({n.borrowing_id for n in notices}) == 2
        assert all(n.type == 'OVERDUE_REMINDER' and 'Python Fundamentals' in n.message and 'Philippine time' in n.message for n in notices)
        assert db.scalar(select(func.count(EmailDelivery.id))) == 2


def test_future_exact_due_and_returned_loans_are_not_overdue(db_factory):
    now = datetime.now(timezone.utc)
    with db_factory() as db:
        add_loan(db, due=now+timedelta(days=1))
        add_loan(db, 2, due=now)
        add_loan(db, due=now-timedelta(days=1), status='RETURNED', returned_at=now)
        assert queue_overdue_reminders(db, now=now) == 0
        assert queue_overdue_reminders(db, now=now+timedelta(microseconds=1)) == 1


def test_member_without_email_still_gets_private_in_app_notice(db_factory):
    with db_factory() as db:
        db.get(User, 1).email = None
        add_loan(db)
        assert queue_overdue_reminders(db) == 1
        assert db.scalar(select(func.count(Notification.id))) == 1
        assert db.scalar(select(func.count(EmailDelivery.id))) == 0


@pytest.mark.parametrize('change', ['returned', 'extended'])
def test_stale_reminder_is_withheld_before_transport(db_factory, smtp, change):
    with db_factory() as db:
        loan = add_loan(db)
        queue_overdue_reminders(db)
        if change == 'returned':
            loan.status = 'RETURNED'
            loan.returned_at = datetime.now(timezone.utc)
        else:
            loan.due_at = datetime.now(timezone.utc)+timedelta(days=1)
        db.commit()
    assert email_worker.process() == 1
    assert smtp == []
    with db_factory() as db:
        item = db.scalar(select(EmailDelivery))
        assert item.status == 'FAILED' and 'no longer overdue' in item.error


def test_valid_overdue_email_uses_the_existing_queue_and_transport(db_factory, smtp):
    with db_factory() as db:
        add_loan(db)
        queue_overdue_reminders(db)
        db.commit()
    assert email_worker.process() == 1
    assert len(smtp) == 1
    assert smtp[0]['Subject'] == 'LIBRAI: Your borrowed book is overdue'
    assert 'Python Fundamentals' in smtp[0].get_content()
    assert 'Philippine time (UTC+08:00)' in smtp[0].get_content()
    assert not list(smtp[0].iter_attachments())


def test_api_poll_queues_reminders_without_autosending(db_factory, monkeypatch):
    with db_factory() as db:
        add_loan(db)
        db.commit()
    monkeypatch.setattr(email_dispatch, 'SessionLocal', db_factory)
    monkeypatch.setattr(settings, 'overdue_notifications_enabled', True)
    monkeypatch.setattr(settings, 'email_autosend_enabled', False)
    monkeypatch.setattr(email_dispatch, 'process', lambda **kwargs: pytest.fail('Autosend disabled'))
    class Stop:
        stopped = False
        def is_set(self): return self.stopped
        def wait(self, seconds): self.stopped = True
    email_dispatch.poll(Stop())
    with db_factory() as db:
        assert db.scalar(select(EmailDelivery)).status == 'PENDING'


def test_rollback_does_not_lose_future_reminder(db_factory):
    with db_factory() as db:
        add_loan(db)
        db.commit()
        assert queue_overdue_reminders(db) == 1
        db.rollback()
    with db_factory() as db:
        assert queue_overdue_reminders(db) == 1


def test_database_rejects_duplicate_overdue_notice(db_factory):
    with db_factory() as db:
        loan = add_loan(db)
        queue_overdue_reminders(db)
        db.commit()
        db.add(Notification(user_id=1, borrowing_id=loan.id, type='OVERDUE_REMINDER', message='Duplicate'))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        assert db.scalar(select(func.count(Notification.id))) == 1


def test_automatic_poll_creates_and_sends_one_overdue_notice(db_factory, smtp, monkeypatch):
    with db_factory() as db:
        add_loan(db)
        db.commit()
    monkeypatch.setattr(email_dispatch, 'SessionLocal', db_factory)
    monkeypatch.setattr(settings, 'overdue_notifications_enabled', True)
    monkeypatch.setattr(settings, 'email_autosend_enabled', True)
    class Stop:
        stopped = False
        def is_set(self): return self.stopped
        def wait(self, seconds): self.stopped = True
    email_dispatch.poll(Stop())
    assert len(smtp) == 1 and 'overdue' in smtp[0]['Subject']
    with db_factory() as db:
        assert db.scalar(select(EmailDelivery)).status == 'SENT'
