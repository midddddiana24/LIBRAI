from datetime import datetime, timedelta, timezone
from backend.models.entities import Borrowing
from backend.models.entities import User, Reservation
from backend.tests.conftest import qr_grants


def test_overdue_filter_includes_unmarked_active_loans_only(client, db_factory, auth_headers):
    now = datetime.now(timezone.utc)
    with db_factory() as db:
        db.add_all([
            Borrowing(user_id=1, book_copy_id=1, due_at=now-timedelta(days=1), status='ACTIVE'),
            Borrowing(user_id=1, book_copy_id=2, due_at=now+timedelta(days=1), status='ACTIVE'),
            Borrowing(user_id=1, book_copy_id=2, due_at=now-timedelta(days=5), returned_at=now, status='RETURNED'),
        ])
        db.commit()
    assert client.get('/api/v1/borrowings?overdue=true').status_code == 401
    result = client.get('/api/v1/borrowings?overdue=true', headers=auth_headers)
    assert result.status_code == 200
    assert result.json()['total'] == 1
    assert result.json()['items'][0]['status'] == 'active'


def test_renewal_projection_explains_waiting_reservation(client, db_factory):
    with db_factory() as db:
        other = User(student_id='OTHER-UX', first_name='Other', last_name='Reader', course='BSIT', year_level='1', status='ACTIVE', qr_token='UX-other-reader')
        db.add(other); db.flush()
        db.add(Reservation(user_id=other.id, book_id=1, status='ACTIVE'))
        db.add(Borrowing(user_id=1, book_copy_id=1, due_at=datetime.now(timezone.utc)+timedelta(days=3), status='ACTIVE'))
        db.commit()
    user, _ = qr_grants(client)
    result = client.get('/api/v1/borrowings', params={'user_id':1, 'verification_token':user['verification_token']})
    assert result.status_code == 200
    loan = result.json()['items'][0]
    assert loan['can_renew'] is False
    assert 'waiting reservation' in loan['renewal_unavailable_reason']
