"""Create the first production admin without demo users, books, or QR codes."""

from __future__ import annotations

import os

from sqlalchemy import select

from backend.core.database import SessionLocal
from backend.core.security import hash_password
from backend.models.entities import Admin


def main() -> None:
    username = os.environ.get("LIBRAI_ADMIN_USERNAME", "admin").strip()
    email = os.environ.get("LIBRAI_ADMIN_EMAIL", "").strip()
    password = os.environ.get("LIBRAI_ADMIN_PASSWORD", "")
    if not username or not email or len(password) < 12:
        raise SystemExit("Set LIBRAI_ADMIN_USERNAME, LIBRAI_ADMIN_EMAIL and a LIBRAI_ADMIN_PASSWORD of at least 12 characters.")
    with SessionLocal() as db:
        if db.scalar(select(Admin.id).where(Admin.username == username)):
            raise SystemExit("Admin username already exists; no account was changed.")
        db.add(Admin(username=username, email=email, password_hash=hash_password(password), role="SUPER_ADMIN"))
        db.commit()
    print(f"Created admin account: {username}")


if __name__ == "__main__":
    main()
