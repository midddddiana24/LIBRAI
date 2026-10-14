import pytest
from sqlalchemy import func, select

from backend.core.security import verify_password
from backend.models.entities import Admin, Book, User
from backend.scripts.manage_admin import create_admin, reset_password


def test_admin_management_changes_only_admin_credentials(db_factory):
    with db_factory() as db:
        before = (
            db.scalar(select(func.count()).select_from(Book)),
            db.scalar(select(func.count()).select_from(User)),
        )
        original = db.scalar(select(Admin).where(Admin.username == "admin"))
        old_hash = original.password_hash

        reset_password(db, "admin", "A-New-Private-Password-2026")
        assert verify_password("A-New-Private-Password-2026", original.password_hash)
        assert not verify_password("SecurePass123!", original.password_hash)
        assert original.password_hash != old_hash

        create_admin(db, "second_admin", "second@example.org", "Another-Private-Password-2026")
        second = db.scalar(select(Admin).where(Admin.username == "second_admin"))
        assert second.role == "SUPER_ADMIN"
        assert verify_password("Another-Private-Password-2026", second.password_hash)
        assert before == (
            db.scalar(select(func.count()).select_from(Book)),
            db.scalar(select(func.count()).select_from(User)),
        )


def test_admin_management_refuses_unknown_or_duplicate_accounts(db_factory):
    with db_factory() as db:
        with pytest.raises(ValueError, match="No admin"):
            reset_password(db, "missing", "A-New-Private-Password-2026")
        with pytest.raises(ValueError, match="already exists"):
            create_admin(db, "different", "admin@librai.test", "Another-Private-Password-2026")
        assert db.scalar(select(func.count()).select_from(Admin)) == 1
