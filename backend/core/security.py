from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.database import get_db
from backend.models.entities import Admin, RevokedToken

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(admin: Admin) -> tuple[str, datetime, str]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.access_token_expire_minutes)
    jti = secrets.token_hex(16)
    payload = {"sub": str(admin.id), "role": admin.role, "jti": jti, "iat": now, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256"), expires, jti


def create_kiosk_grant(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(user_id), "purpose": "kiosk_user", "iat": now, "exp": now + timedelta(minutes=5)}, settings.secret_key, algorithm="HS256")


def create_book_grant(copy_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(copy_id), "purpose": "kiosk_book", "iat": now, "exp": now + timedelta(minutes=5)}, settings.secret_key, algorithm="HS256")


def create_user_photo_grant(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "purpose": "user_photo", "iat": now, "exp": now + timedelta(minutes=10)},
        settings.secret_key,
        algorithm="HS256",
    )


def verify_user_photo_grant(token: str) -> int:
    payload = decode_token(token)
    if payload.get("purpose") != "user_photo":
        raise HTTPException(status_code=401, detail="Invalid user photo ticket.")
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid user photo ticket.") from exc


def create_qr_download_grant(entity_type: str, entity_id: int) -> str:
    """Create a short-lived browser-safe ticket for one QR PNG download."""
    if entity_type not in {"user", "book_copy"}:
        raise ValueError("Unsupported QR download entity type.")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(entity_id),
        "entity_type": entity_type,
        "purpose": "qr_download",
        "jti": secrets.token_hex(12),
        "iat": now,
        "exp": now + timedelta(minutes=2),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def verify_qr_download_grant(token: str) -> tuple[str, int]:
    payload = decode_token(token)
    entity_type = payload.get("entity_type")
    if payload.get("purpose") != "qr_download" or entity_type not in {"user", "book_copy"}:
        raise HTTPException(status_code=401, detail="Invalid QR download ticket.")
    try:
        return str(entity_type), int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid QR download ticket.") from exc


def create_report_download_grant(job_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(job_id), "purpose": "report_download", "jti": secrets.token_hex(12), "iat": now, "exp": now + timedelta(minutes=5)},
        settings.secret_key,
        algorithm="HS256",
    )


def verify_report_download_grant(token: str) -> int:
    payload = decode_token(token)
    if payload.get("purpose") != "report_download":
        raise HTTPException(status_code=401, detail="Invalid report download ticket.")
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid report download ticket.") from exc


def verify_kiosk_grant(token: str | None, user_id: int) -> None:
    if not token:
        raise HTTPException(status_code=401, detail="A recent user QR verification is required.")
    payload = decode_token(token)
    if payload.get("purpose") != "kiosk_user" or payload.get("sub") != str(user_id):
        raise HTTPException(status_code=401, detail="The QR verification does not match this user.")


def verify_book_grant(token: str | None, copy_id: int) -> None:
    if not token:
        raise HTTPException(status_code=401, detail="A recent book QR verification is required.")
    payload = decode_token(token)
    if payload.get("purpose") != "kiosk_book" or payload.get("sub") != str(copy_id):
        raise HTTPException(status_code=401, detail="The QR verification does not match this book copy.")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.") from exc


def get_token_payload(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return decode_token(credentials.credentials)


def get_current_admin(payload: dict = Depends(get_token_payload), db: Session = Depends(get_db)) -> Admin:
    if db.scalar(select(RevokedToken).where(RevokedToken.jti == payload.get("jti"))):
        raise HTTPException(status_code=401, detail="This access token has been logged out.")
    admin = db.get(Admin, int(payload["sub"]))
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Admin account is unavailable.")
    return admin


def get_optional_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> Admin | None:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if db.scalar(select(RevokedToken).where(RevokedToken.jti == payload.get("jti"))):
        return None
    admin = db.get(Admin, int(payload["sub"]))
    return admin if admin and admin.is_active else None


def require_super_admin(admin: Admin = Depends(get_current_admin)) -> Admin:
    if admin.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super administrator access required.")
    return admin


def make_qr_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"
