from backend.tests.conftest import qr_grants
from backend.api.v1.qr import qr_png

def test_authentication_login_me_logout(client):
    bad=client.post("/api/v1/auth/login",json={"username":"admin","password":"WrongPassword!"});assert bad.status_code==401
    login=client.post("/api/v1/auth/login",json={"username":"admin","password":"SecurePass123!"});assert login.status_code==200
    headers={"Authorization":f"Bearer {login.json()['access_token']}"};assert client.get("/api/v1/auth/me",headers=headers).status_code==200
    assert client.post("/api/v1/auth/logout",headers=headers).status_code==200
    assert client.get("/api/v1/auth/me",headers=headers).status_code==401

def test_qr_verification_returns_safe_grants(client):
    user,book=qr_grants(client)
    assert user["student_id"]=="2026-0001" and user["can_borrow"] is True and "qr_token" not in user
    assert user["verification_token"] and book["verification_token"] and book["accession_number"]=="BK-00001-C001"
    assert client.post("/api/v1/qr/verify-user",json={"qr_token":"invalid-token-value"}).status_code==404

def test_qr_photo_decoding(client):
    token="USR_QR_test_secure_token_123456"
    decoded=client.post("/api/v1/qr/decode-image",files={"file":("user-qr.png",qr_png(token),"image/png")})
    assert decoded.status_code==200 and decoded.json()["token"]==token
    invalid=client.post("/api/v1/qr/decode-image",files={"file":("bad.png",b"not-an-image","image/png")})
    assert invalid.status_code==422
