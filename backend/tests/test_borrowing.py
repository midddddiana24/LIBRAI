from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
import pytest
from sqlalchemy import select
from backend.core.exceptions import DomainError
from backend.models.entities import BookCopy,Borrowing,BorrowingStatus,CopyStatus,SystemSetting,User
from backend.services.borrowing_service import borrow_book
from backend.tests.conftest import qr_grants

def borrow_payload(client):
    user,book=qr_grants(client);return {"user_id":user["id"],"book_copy_id":book["id"],"user_verification_token":user["verification_token"],"book_verification_token":book["verification_token"]}

def test_borrow_and_return_success(client):
    payload=borrow_payload(client);response=client.post("/api/v1/borrowings",json=payload);assert response.status_code==201;receipt=response.json();assert receipt["status"]=="active"
    notifications=client.get("/api/v1/notifications",params={"user_id":payload["user_id"],"verification_token":payload["user_verification_token"]});assert notifications.status_code==200 and notifications.json()
    notification_id=notifications.json()[0]["id"]
    marked=client.post(f"/api/v1/notifications/{notification_id}/read",json={"verification_token":payload["user_verification_token"]});assert marked.status_code==200 and marked.json()["is_read"] is True
    assert client.get("/api/v1/notifications",params={"user_id":payload["user_id"]}).status_code==401
    book=client.post("/api/v1/qr/verify-book",json={"qr_token":"BOOK_QR_test_secure_token_12345"}).json()
    returned=client.post("/api/v1/returns",json={"borrowing_id":receipt["id"],"book_verification_token":book["verification_token"]});assert returned.status_code==201 and returned.json()["return_status"] in {"on_time","overdue"}

def test_borrow_requires_matching_qr_grants(client):
    payload=borrow_payload(client);payload["user_verification_token"]=None
    assert client.post("/api/v1/borrowings",json=payload).status_code==401

def test_borrowing_renewal_success_and_limit(client):
    payload=borrow_payload(client)
    receipt=client.post("/api/v1/borrowings",json=payload).json()
    renewed=client.post(f"/api/v1/borrowings/{receipt['id']}/renew",json={"user_id":payload["user_id"],"user_verification_token":payload["user_verification_token"]})
    assert renewed.status_code==200
    assert renewed.json()["renewal_count"]==1
    assert renewed.json()["due_at"]>receipt["due_at"]
    limited=client.post(f"/api/v1/borrowings/{receipt['id']}/renew",json={"user_id":payload["user_id"],"user_verification_token":payload["user_verification_token"]})
    assert limited.status_code==409
    assert limited.json()["error"]["code"]=="RENEWAL_LIMIT_REACHED"

def test_return_rejects_wrong_book_qr(client):
    payload=borrow_payload(client);receipt=client.post("/api/v1/borrowings",json=payload).json()
    other=client.post("/api/v1/qr/verify-book",json={"qr_token":"BOOK_QR_second_secure_token_123"}).json()
    response=client.post("/api/v1/returns",json={"borrowing_id":receipt["id"],"book_verification_token":other["verification_token"]})
    assert response.status_code==401

def test_inactive_user_unavailable_limit_and_overdue(db_factory):
    with db_factory() as db:
        user=db.scalar(select(User));copy=db.scalar(select(BookCopy).where(BookCopy.accession_number=="BK-00001-C001"));user.status="INACTIVE";db.commit()
        with pytest.raises(DomainError,match="not active"):borrow_book(db,user.id,copy.id)
        user.status="ACTIVE";copy.status=CopyStatus.BORROWED;db.commit()
        with pytest.raises(DomainError,match="not available"):borrow_book(db,user.id,copy.id)
        copy.status=CopyStatus.AVAILABLE;db.add(SystemSetting(key="BORROWING_LIMIT",value="0"));db.commit()
        with pytest.raises(DomainError,match="borrowing limit"):borrow_book(db,user.id,copy.id)
        db.query(SystemSetting).filter_by(key="BORROWING_LIMIT").update({"value":"3"});db.add(Borrowing(user_id=user.id,book_copy_id=copy.id,borrowed_at=datetime.now(timezone.utc)-timedelta(days=10),due_at=datetime.now(timezone.utc)-timedelta(days=3),status=BorrowingStatus.ACTIVE));copy.status=CopyStatus.BORROWED;second=db.scalar(select(BookCopy).where(BookCopy.accession_number=="BK-00001-C002"));db.commit()
        with pytest.raises(DomainError,match="overdue"):borrow_book(db,user.id,second.id)

def test_concurrent_borrowing_only_one_succeeds(db_factory):
    with db_factory() as db:user_id=db.scalar(select(User.id));copy_id=db.scalar(select(BookCopy.id))
    def attempt():
        with db_factory() as db:
            try:borrow_book(db,user_id,copy_id);return "success"
            except DomainError:return "conflict"
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:attempt(),range(2)))
    assert results.count("success")==1 and results.count("conflict")==1
