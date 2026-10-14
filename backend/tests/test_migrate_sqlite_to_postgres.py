from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select

from backend.core.database import Base
from backend.models.entities import Admin, Book, BookCopy, User
from backend.scripts.migrate_sqlite_to_postgres import copy_records


def add_revision(engine):
    with engine.begin() as db:
        db.exec_driver_sql("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        db.exec_driver_sql("INSERT INTO alembic_version (version_num) VALUES ('same-revision')")


def test_copies_all_records_and_preserves_identifiers(db_factory, tmp_path):
    source = db_factory.kw["bind"]
    target = create_engine(f"sqlite:///{tmp_path / 'target.db'}")
    Base.metadata.create_all(target)
    add_revision(source)
    add_revision(target)

    counts = copy_records(source, target)

    assert counts["admins"] == 1
    assert counts["users"] == 1
    assert counts["books"] == 1
    assert counts["book_copies"] == 2
    with source.connect() as original, target.connect() as copied:
        assert copied.scalar(select(Admin.password_hash)) == original.scalar(select(Admin.password_hash))
        assert copied.scalar(select(User.id)) == original.scalar(select(User.id))
        assert copied.scalar(select(Book.id)) == original.scalar(select(Book.id))
        assert copied.scalar(select(Book.keywords)) == original.scalar(select(Book.keywords))
        assert copied.scalar(select(func.count()).select_from(BookCopy)) == 2
    target.dispose()


def test_refuses_to_merge_into_nonempty_target(db_factory, tmp_path):
    source = db_factory.kw["bind"]
    target = create_engine(f"sqlite:///{tmp_path / 'target.db'}")
    Base.metadata.create_all(target)
    add_revision(source)
    add_revision(target)
    with target.begin() as db:
        db.execute(
            Admin.__table__.insert().values(
                id=99,
                username="existing",
                email="existing@example.org",
                password_hash="preserve-this-hash",
                role="SUPER_ADMIN",
                is_active=True,
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
    with pytest.raises(ValueError, match="already has records"):
        copy_records(source, target)
    with target.connect() as db:
        assert db.scalar(select(func.count()).select_from(Admin)) == 1
        assert db.scalar(select(func.count()).select_from(User)) == 0
    target.dispose()
