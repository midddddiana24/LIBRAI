from __future__ import annotations
from datetime import datetime,timedelta,timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.core.database import Base,get_db
from backend.core.security import hash_password
from backend.main import app
from backend.models.entities import Admin,Book,BookCopy,Category,CopyStatus,User

@pytest.fixture()
def db_factory(tmp_path):
    engine=create_engine(f"sqlite:///{tmp_path/'test.db'}",connect_args={"check_same_thread":False,"timeout":10})
    Base.metadata.create_all(engine);factory=sessionmaker(bind=engine,expire_on_commit=False)
    with factory() as db:
        admin=Admin(username="admin",email="admin@librai.test",password_hash=hash_password("SecurePass123!"),role="SUPER_ADMIN")
        user=User(student_id="2026-0001",first_name="Test",last_name="Student",course="BSIT",year_level="3",email="student@librai.test",qr_token="USR_QR_test_secure_token_123456",status="ACTIVE")
        category=Category(name="Computer Science");book=Book(isbn="9780000000001",title="Python Fundamentals",author="Test Author",publisher="LIBRAI Press",publication_year=2026,category=category,description="Beginner Python programming",keywords=["python","beginner"],subjects=["programming"],shelf_location="CS-001")
        copy1=BookCopy(book=book,accession_number="BK-00001-C001",qr_token="BOOK_QR_test_secure_token_12345",status=CopyStatus.AVAILABLE)
        copy2=BookCopy(book=book,accession_number="BK-00001-C002",qr_token="BOOK_QR_second_secure_token_123",status=CopyStatus.AVAILABLE)
        db.add_all([admin,user,category,book,copy1,copy2]);db.commit()
    yield factory
    engine.dispose()

@pytest.fixture()
def client(db_factory):
    def override():
        db=db_factory()
        try:yield db
        finally:db.close()
    app.dependency_overrides[get_db]=override
    with TestClient(app) as c:yield c
    app.dependency_overrides.clear()

@pytest.fixture()
def auth_headers(client):
    response=client.post("/api/v1/auth/login",json={"username":"admin","password":"SecurePass123!"})
    assert response.status_code==200
    return {"Authorization":f"Bearer {response.json()['access_token']}"}

def qr_grants(client):
    user=client.post("/api/v1/qr/verify-user",json={"qr_token":"USR_QR_test_secure_token_123456"}).json()
    book=client.post("/api/v1/qr/verify-book",json={"qr_token":"BOOK_QR_test_secure_token_12345"}).json()
    return user,book
