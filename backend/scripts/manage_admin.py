"""Create an admin or reset its password in the database used by this process.

Run this only where DATABASE_URL points to the intended database. Passwords are
entered interactively so they do not appear in shell history or arguments.
"""

from __future__ import annotations

import argparse
import getpass
import sys

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.core.security import hash_password
from backend.models.entities import Admin, AdminRole


def create_admin(db: Session, username: str, email: str, password: str) -> None:
    username, email = username.strip(), email.strip()
    if not username or not email or "@" not in email:
        raise ValueError("A username and valid email address are required.")
    if len(password) < 12:
        raise ValueError("The new password must have at least 12 characters.")
    if db.scalar(select(Admin.id).where(or_(Admin.username == username, Admin.email == email))):
        raise ValueError("That admin username or email address already exists.")
    db.add(Admin(username=username, email=email, password_hash=hash_password(password), role=AdminRole.SUPER_ADMIN))
    db.commit()


def reset_password(db: Session, username: str, password: str) -> None:
    if len(password) < 12:
        raise ValueError("The new password must have at least 12 characters.")
    admin = db.scalar(select(Admin).where(Admin.username == username.strip()))
    if admin is None:
        raise ValueError("No admin has that username; no account was changed.")
    if not admin.is_active:
        raise ValueError("That admin is disabled; resetting its password would not enable login.")
    admin.password_hash = hash_password(password)
    db.commit()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="Create a new super admin without demo records")
    create.add_argument("--username", required=True)
    create.add_argument("--email", required=True)
    reset = commands.add_parser("reset-password", help="Set a new password for an existing admin")
    reset.add_argument("--username", required=True)
    args = parser.parse_args(argv)

    if not sys.stdin.isatty():
        raise SystemExit("An interactive terminal is required for password entry.")
    password = getpass.getpass("New admin password (at least 12 characters): ")
    confirmation = getpass.getpass("Confirm new admin password: ")
    if password != confirmation:
        raise SystemExit("Passwords did not match; no account was changed.")
    try:
        with SessionLocal() as db:
            if args.command == "create":
                create_admin(db, args.username, args.email, password)
                print(f"Created admin account: {args.username.strip()}")
            else:
                reset_password(db, args.username, password)
                print(f"Reset password for admin account: {args.username.strip()}")
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
