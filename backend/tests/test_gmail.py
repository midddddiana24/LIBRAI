import base64
from email import policy
from email.parser import BytesParser
import json
import threading
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen

import httpx
import pytest
from sqlalchemy import select

from backend.core.config import settings
from backend.models.entities import EmailDelivery, User
from backend.scripts import authorize_gmail, email_worker
from backend.services import gmail_service, email_dispatch
from backend.services.notification_service import queue_library_id, notify_user


@pytest.fixture()
def gmail(monkeypatch, tmp_path, db_factory):
    data = {'type':'authorized_user', 'client_id':'fake-client', 'client_secret':'private-test-client', 'refresh_token':'private-test-refresh', 'sender':'library@example.com', 'scopes':[gmail_service.SCOPE]}
    path = tmp_path / 'oauth.json'; path.write_text(json.dumps(data))
    monkeypatch.setattr(settings, 'email_transport', 'gmail_api')
    monkeypatch.setattr(settings, 'gmail_oauth_file', path)
    monkeypatch.setattr(email_worker, 'SessionLocal', db_factory)
    requests = []
    def handler(request):
        requests.append(request)
        if str(request.url) == gmail_service.TOKEN_URL:
            return httpx.Response(200, json={'access_token':'private-test-access'})
        assert str(request.url) == gmail_service.SEND_URL
        assert request.headers['authorization'] == 'Bearer private-test-access'
        return httpx.Response(200, json={'id':'accepted-message'})
    original = httpx.Client
    monkeypatch.setattr(gmail_service.httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    return data, requests, original


def test_gmail_sends_mime_qr_via_https_and_marks_sent(db_factory, gmail):
    with db_factory() as db:
        queue_library_id(db, db.get(User, 1)); db.commit()
    assert email_worker.configured()
    assert email_worker.process() == 1
    data, requests, _ = gmail
    encoded = json.loads(requests[1].content)['raw']
    message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(encoded))
    assert str(message['From']) == data['sender']
    assert str(message['To']) == 'student@librai.test'
    assert list(message.iter_attachments())[0].get_filename() == 'library-id.png'
    with db_factory() as db:
        assert db.scalar(select(EmailDelivery)).status == 'SENT'


@pytest.mark.parametrize('fail_at', ['token', 'send', 'missing_id', 'timeout'])
def test_gmail_failures_never_mark_sent_or_store_secrets(db_factory, gmail, monkeypatch, fail_at):
    _, requests, original = gmail
    def handler(request):
        requests.append(request)
        if fail_at == 'timeout': raise httpx.ReadTimeout('private-test-refresh')
        if str(request.url) == gmail_service.TOKEN_URL:
            return httpx.Response(400 if fail_at == 'token' else 200, json={'access_token':'private-test-access', 'error_description':'private-test-refresh'})
        return httpx.Response(403 if fail_at == 'send' else 200, json={})
    monkeypatch.setattr(gmail_service.httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    with db_factory() as db:
        queue_library_id(db, db.get(User, 1)); db.commit()
    assert email_worker.process() == 1
    with db_factory() as db:
        item = db.scalar(select(EmailDelivery))
        assert item.status == 'FAILED' and item.sent_at is None
        assert 'private-test' not in item.error
    assert email_worker.process() == 0  # No automatic retry of failed deliveries.


def test_staff_send_one_is_authenticated_and_does_not_drain_queue(client, auth_headers, db_factory, gmail):
    with db_factory() as db:
        notify_user(db, 1, 'RETURN_SUCCESS', 'Earlier pending notice'); db.flush()
        queue_library_id(db, db.get(User, 1)); db.flush()
        ids = db.scalars(select(EmailDelivery.id).order_by(EmailDelivery.id)).all(); db.commit()
    path = f'/api/v1/notifications/admin/email-deliveries/{ids[1]}/send'
    assert client.post(path).status_code == 401
    assert client.post(path, headers=auth_headers).status_code == 202
    assert client.post(path, headers=auth_headers).status_code == 409
    with db_factory() as db:
        assert db.get(EmailDelivery, ids[0]).status == 'PENDING'
        assert db.get(EmailDelivery, ids[1]).status == 'SENT'
    status = client.get('/api/v1/notifications/admin/email-status', headers=auth_headers).json()
    assert status['transport'] == 'gmail_api' and status['email_configured'] is True
    assert status['autosend_enabled'] is False
    assert 'private-test' not in str(status)


def test_missing_credentials_leave_pending_and_reject_dispatch(client, auth_headers, db_factory, gmail, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'gmail_oauth_file', tmp_path/'absent.json')
    with db_factory() as db:
        queue_library_id(db, db.get(User, 1)); db.flush()
        uid = db.scalar(select(EmailDelivery.id)); db.commit()
    assert not email_worker.configured()
    assert client.post(f'/api/v1/notifications/admin/email-deliveries/{uid}/send', headers=auth_headers).status_code == 503
    with db_factory() as db: assert db.get(EmailDelivery, uid).status == 'PENDING'


def test_poll_dispatches_committed_work_and_stops_without_sleep(db_factory, gmail):
    with db_factory() as db:
        queue_library_id(db, db.get(User, 1)); db.commit()
    class Stop:
        stopped = False
        def is_set(self): return self.stopped
        def wait(self, seconds): assert seconds == 30; self.stopped = True
    email_dispatch.poll(Stop())
    with db_factory() as db: assert db.scalar(select(EmailDelivery)).status == 'SENT'


def test_authorization_checks_state_pkce_and_saves_only_private_refresh_token(monkeypatch, tmp_path, capsys):
    client_file = tmp_path/'client.json'
    client_file.write_text(json.dumps({'installed':{'client_id':'test-client', 'client_secret':'test-secret'}}))
    output = tmp_path/'private'/'oauth.json'
    original = httpx.Client
    def exchange(request):
        assert str(request.url) == gmail_service.TOKEN_URL
        fields = parse_qs(request.content.decode())
        assert fields['code'] == ['test-code'] and len(fields['code_verifier'][0]) >= 43
        return httpx.Response(200, json={'refresh_token':'test-private-refresh', 'access_token':'do-not-save-access', 'scope':gmail_service.SCOPE})
    monkeypatch.setattr(authorize_gmail.httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(exchange), **kwargs))
    callbacks = []
    def open_browser(url):
        params = parse_qs(urlparse(url).query)
        assert params['scope'] == [gmail_service.SCOPE] and params['code_challenge_method'] == ['S256']
        def callback():
            redirect = params['redirect_uri'][0]
            try:
                urlopen(redirect+'?'+urlencode({'state':'wrong-state', 'code':'wrong'})).close()
            except Exception: pass
            with urlopen(redirect+'?'+urlencode({'state':params['state'][0], 'code':'test-code'})) as response:
                callbacks.append(response.status)
        threading.Thread(target=callback, daemon=True).start()
        return True
    monkeypatch.setattr(authorize_gmail.webbrowser, 'open', open_browser)
    authorize_gmail.authorize(client_file, 'library@example.com', output, timeout=10)
    saved = json.loads(output.read_text())
    assert saved['refresh_token'] == 'test-private-refresh'
    assert 'access_token' not in saved and callbacks == [200]
    captured = capsys.readouterr().out
    assert all(value not in captured for value in ['test-private-refresh', 'test-secret'])
    with pytest.raises(ValueError, match='already exists'):
        authorize_gmail.authorize(client_file, 'library@example.com', output)
