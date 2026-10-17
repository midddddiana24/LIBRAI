from sqlalchemy import func, select

from backend.core.security import create_book_grant, create_kiosk_grant
from backend.models.entities import AuditLog, User

DETAILS = {"student_id": "25-1234", "library_card_number": "25-9876", "first_name": "Juan P.", "last_name": "Dela Cruz Jr.", "course": "BS Information Technology", "year_level": "3", "email": ""}


def test_kiosk_registration_requires_staff_approval(client, db_factory, auth_headers):
    result = client.post('/api/v1/registrations', json=DETAILS)
    assert result.status_code == 202 and set(result.json()) == {'message'}
    with db_factory() as db:
        user = db.scalar(select(User).where(User.student_id == DETAILS['student_id']))
        uid, token = user.id, user.qr_token
        assert user.status == 'PENDING' and user.library_card_number == DETAILS['library_card_number']
        assert user.email is None
    pending = client.get('/api/v1/users?status=PENDING&q=9876', headers=auth_headers).json()
    assert pending['total'] == 1 and pending['items'][0]['can_borrow'] is False
    assert client.get(f'/api/v1/users/{uid}/qr', headers=auth_headers).status_code == 403
    assert client.post(f'/api/v1/users/{uid}/qr', headers=auth_headers).status_code == 403
    assert client.post('/api/v1/qr/verify-user', json={'token': token}).status_code == 403
    borrow = client.post('/api/v1/borrowings', json={'user_id': uid, 'book_copy_id': 1, 'user_verification_token': create_kiosk_grant(uid), 'book_verification_token': create_book_grant(1)})
    assert borrow.status_code >= 400
    assert client.put(f'/api/v1/users/{uid}', json={'status': 'ACTIVE'}).status_code == 401
    approved = client.put(f'/api/v1/users/{uid}', headers=auth_headers, json={'status': 'ACTIVE'})
    assert approved.status_code == 200 and approved.json()['can_borrow'] is True
    assert client.get(f'/api/v1/users/{uid}/qr', headers=auth_headers).status_code == 200
    with db_factory() as db:
        actions = set(db.scalars(select(AuditLog.action)).all())
        assert {'REGISTRATION_REQUESTED', 'REGISTRATION_APPROVED'} <= actions


def test_public_registration_never_overwrites_or_exposes_existing_members(client, db_factory):
    existing = {**DETAILS, 'student_id': '2026-0001', 'first_name': 'Overwrite attempt'}
    duplicate = client.post('/api/v1/registrations', json=existing)
    fresh = client.post('/api/v1/registrations', json=DETAILS)
    repeated = client.post('/api/v1/registrations', json=DETAILS)
    assert duplicate.status_code == fresh.status_code == repeated.status_code == 202
    assert duplicate.json() == fresh.json() == repeated.json()
    with db_factory() as db:
        original = db.scalar(select(User).where(User.student_id == '2026-0001'))
        assert original.first_name == 'Test' and original.status == 'ACTIVE'
        assert db.scalar(select(func.count()).select_from(User)) == 2


def test_public_registration_cannot_set_privileged_fields(client):
    for extra in [{'status': 'ACTIVE'}, {'qr_token': 'attacker-chosen-token'}, {'role': 'SUPER_ADMIN'}]:
        assert client.post('/api/v1/registrations', json={**DETAILS, **extra}).status_code == 422


def test_library_number_uniqueness_is_enforced_on_staff_edits(client, auth_headers):
    created = client.post('/api/v1/users', headers=auth_headers, json=DETAILS)
    assert created.status_code == 201
    conflict = client.put('/api/v1/users/1', headers=auth_headers, json={'library_card_number': DETAILS['library_card_number']})
    assert conflict.status_code == 409
    assert client.get('/api/v1/users/1', headers=auth_headers).json()['library_card_number'] is None


def test_staff_can_reject_without_activating(client, auth_headers):
    client.post('/api/v1/registrations', json=DETAILS)
    uid = client.get('/api/v1/users?status=PENDING', headers=auth_headers).json()['items'][0]['id']
    rejected = client.put(f'/api/v1/users/{uid}', headers=auth_headers, json={'status': 'INACTIVE'})
    assert rejected.status_code == 200 and rejected.json()['can_borrow'] is False
    assert client.get('/api/v1/users?status=PENDING', headers=auth_headers).json()['total'] == 0


def test_public_registration_has_request_limit(client, monkeypatch):
    from backend.core.config import settings
    from backend.main import requests_by_ip
    monkeypatch.setattr(settings, 'rate_limit_requests_per_window', 1)
    requests_by_ip.clear()
    try:
        assert client.post('/api/v1/registrations', json={}).status_code == 422
        assert client.post('/api/v1/registrations', json={}).status_code == 429
    finally:
        requests_by_ip.clear()
