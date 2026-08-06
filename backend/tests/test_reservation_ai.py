from sqlalchemy import select
from backend.ai.gemini_client import gemini_client
from backend.models.entities import BookCopy,CopyStatus
from backend.tests.conftest import qr_grants

def test_reservation_creation(client,db_factory):
    with db_factory() as db:
        for copy in db.scalars(select(BookCopy)):copy.status=CopyStatus.BORROWED
        db.commit()
    user,_=qr_grants(client)
    response=client.post("/api/v1/reservations",json={"user_id":user["id"],"book_id":1,"user_verification_token":user["verification_token"]})
    assert response.status_code==201 and response.json()["position"]==1
    duplicate=client.post("/api/v1/reservations",json={"user_id":user["id"],"book_id":1,"user_verification_token":user["verification_token"]});assert duplicate.status_code==409
    cancelled=client.delete(f"/api/v1/reservations/{response.json()['id']}",params={"verification_token":user["verification_token"]})
    assert cancelled.status_code==200 and cancelled.json()["status"]=="cancelled"


def test_reservation_rejects_title_without_physical_copies(client,db_factory):
    user=client.post("/api/v1/qr/verify-user",json={"qr_token":"USR_QR_test_secure_token_123456"}).json()
    with db_factory() as db:
        for copy in db.scalars(select(BookCopy)).all():db.delete(copy)
        db.commit()
    response=client.post("/api/v1/reservations",json={"user_id":user["id"],"book_id":1,"user_verification_token":user["verification_token"]})
    assert response.status_code==409
    assert response.json()["error"]["code"]=="BOOK_HAS_NO_COPIES"

def test_ai_database_fallback(client,monkeypatch):
    monkeypatch.setattr(gemini_client,"rank",lambda *_args,**_kwargs:None)
    response=client.post("/api/v1/ai/search",json={"query":"beginner Python programming"});assert response.status_code==200
    data=response.json();assert data["fallback_used"] is True and data["ai_available"] is False and data["books"][0]["id"]==1
    assert data["parsed_intent"]["level"]=="beginner"
    assert "python" in data["parsed_intent"]["topics"]
    feedback=client.post("/api/v1/ai/feedback",json={"interaction_id":data["interaction_id"],"helpful":True})
    assert feedback.status_code==201
