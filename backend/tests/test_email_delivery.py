import cv2
import numpy as np
import pytest
from sqlalchemy import select

from backend.core.config import settings
from backend.models.entities import EmailDelivery, Notification, User
from backend.scripts import email_worker
from backend.services.notification_service import queue_library_id, notify_user


@pytest.fixture()
def smtp(monkeypatch, db_factory):
    messages = []
    class Server:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def starttls(self, *, context): assert context.check_hostname
        def login(self, username, password): assert password == 'test-app-password'
        def send_message(self, message):
            messages.append(message)
            return {}
    for key, value in dict(smtp_host='smtp.example.invalid', smtp_port=587, smtp_username='library@example.invalid', smtp_password='test-app-password', smtp_from='library@example.invalid', smtp_use_tls=True).items():
        monkeypatch.setattr(settings, key, value)
    monkeypatch.setattr(email_worker, 'SessionLocal', db_factory)
    monkeypatch.setattr(email_worker.smtplib, 'SMTP', Server)
    monkeypatch.setattr(email_worker.smtplib, 'SMTP_SSL', Server)
    return messages


def test_approval_queues_one_qr_and_worker_sends_decodable_current_id(client, auth_headers, db_factory, smtp):
    details = dict(student_id='25-1122', first_name='Sample', last_name='Reader', course='BSIT', year_level='1', email='sample@example.com')
    assert client.post('/api/v1/registrations', json=details).status_code == 202
    with db_factory() as db:
        user = db.scalar(select(User).where(User.student_id == details['student_id']))
        uid = user.id
        assert db.scalar(select(EmailDelivery)) is None
    assert client.put(f'/api/v1/users/{uid}', headers=auth_headers, json={'status':'ACTIVE'}).status_code == 200
    assert client.put(f'/api/v1/users/{uid}', headers=auth_headers, json={'course':'BSCS'}).status_code == 200
    assert client.post(f'/api/v1/users/{uid}/email-qr', headers=auth_headers).status_code == 202
    with db_factory() as db:
        assert len(db.scalars(select(EmailDelivery)).all()) == 1
        # A replacement before dispatch must use the current QR, never a stale token.
        user = db.get(User, uid)
        user.qr_token = 'USR_QR_replaced_current_token_test'
        db.commit()
    assert email_worker.process() == 1
    attachment = list(smtp[0].iter_attachments())[0]
    assert attachment.get_filename() == 'library-id.png'
    image = cv2.imdecode(np.frombuffer(attachment.get_payload(decode=True), np.uint8), cv2.IMREAD_COLOR)
    token, _, _ = cv2.QRCodeDetector().detectAndDecode(image)
    assert token == 'USR_QR_replaced_current_token_test'
    assert token not in smtp[0].get_body(preferencelist=('plain',)).get_content()
    assert client.post('/api/v1/qr/verify-user', json={'token':token}).status_code == 200
    with db_factory() as db:
        item = db.scalar(select(EmailDelivery))
        assert item.status == 'SENT' and item.sent_at is not None
    assert email_worker.process() == 0


@pytest.mark.parametrize('change', ['status', 'email'])
def test_qr_withheld_after_account_or_email_changes(db_factory, smtp, change):
    with db_factory() as db:
        user = db.get(User, 1)
        queue_library_id(db, user)
        db.commit()
        if change == 'status': user.status = 'INACTIVE'
        else: user.email = 'changed@example.com'
        db.commit()
    assert email_worker.process() == 1 and smtp == []
    with db_factory() as db: assert db.scalar(select(EmailDelivery)).status == 'FAILED'


def test_smtp_failure_is_persistent_redacted_and_staff_can_retry(client, auth_headers, db_factory, smtp, monkeypatch):
    with db_factory() as db:
        queue_library_id(db, db.get(User, 1)); db.commit()
    def fail(*args, **kwargs): raise OSError('test-app-password must never be stored')
    original = email_worker.smtplib.SMTP
    monkeypatch.setattr(email_worker.smtplib, 'SMTP', fail)
    assert email_worker.process() == 1
    with db_factory() as db:
        item = db.scalar(select(EmailDelivery)); delivery_id = item.id
        assert item.status == 'FAILED' and 'test-app-password' not in item.error
    path = f'/api/v1/notifications/admin/email-deliveries/{delivery_id}/retry'
    assert client.post(path).status_code == 401
    assert client.post(path, headers=auth_headers).status_code == 202
    assert client.post(path, headers=auth_headers).status_code == 409
    monkeypatch.setattr(email_worker.smtplib, 'SMTP', original)
    assert email_worker.process() == 1 and len(smtp) == 1
    assert client.post(path, headers=auth_headers).status_code == 409
    listing = client.get('/api/v1/notifications/admin/email-deliveries', headers=auth_headers).json()
    assert listing['items'][0]['status'] == 'sent'
    assert 'body' not in listing['items'][0]


def test_staff_creation_and_resend_require_active_email(client, auth_headers, db_factory, smtp):
    assert client.post('/api/v1/users/1/email-qr').status_code == 401
    details = dict(student_id='25-3344', first_name='Example', last_name='Member', course='BSIT', year_level='2', email='new@example.com')
    created = client.post('/api/v1/users', headers=auth_headers, json=details)
    assert created.status_code == 201
    uid = created.json()['id']
    assert email_worker.process() == 1
    assert client.post(f'/api/v1/users/{uid}/email-qr', headers=auth_headers).status_code == 202
    assert email_worker.process() == 1
    assert len(smtp) == 2
    client.put(f'/api/v1/users/{uid}', headers=auth_headers, json={'status':'PENDING'})
    assert client.post(f'/api/v1/users/{uid}/email-qr', headers=auth_headers).status_code == 409


def test_existing_notification_emails_and_ssl_transport(db_factory, smtp, monkeypatch):
    with db_factory() as db:
        notify_user(db, 1, 'RETURN_SUCCESS', 'Your book was returned.')
        db.commit()
    monkeypatch.setattr(settings, 'smtp_port', 465)
    assert email_worker.process() == 1
    assert not list(smtp[0].iter_attachments())
    assert 'Your book was returned.' in smtp[0].get_content()


def test_controlled_test_sends_only_selected_delivery(db_factory, smtp):
    with db_factory() as db:
        notify_user(db, 1, 'RETURN_SUCCESS', 'Older pending message')
        db.flush()
        queue_library_id(db, db.get(User, 1)); db.flush()
        items = db.scalars(select(EmailDelivery).order_by(EmailDelivery.id)).all()
        older_id, test_id = items[0].id, items[1].id
        db.commit()
    assert email_worker.process(delivery_id=test_id) == 1
    assert len(smtp) == 1 and list(smtp[0].iter_attachments())
    with db_factory() as db:
        assert db.get(EmailDelivery, older_id).status == 'PENDING'
        assert db.get(EmailDelivery, test_id).status == 'SENT'


def test_email_configuration_is_private_and_tls_required(client, auth_headers, smtp, monkeypatch):
    path = '/api/v1/notifications/admin/email-status'
    assert client.get(path).status_code == 401
    body = client.get(path, headers=auth_headers).json()
    assert body['smtp_configured'] is True and 'password' not in str(body)
    monkeypatch.setattr(settings, 'smtp_use_tls', False)
    with pytest.raises(RuntimeError, match='STARTTLS'): email_worker.process()
    monkeypatch.setattr(settings, 'smtp_password', None)
    with pytest.raises(RuntimeError, match='SMTP_HOST'): email_worker.process()
