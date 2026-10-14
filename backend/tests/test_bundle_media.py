import sqlite3
import zipfile

import pytest

from backend.scripts.bundle_media import bundle


def test_bundles_only_referenced_private_and_public_media(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "generated"
    paths = [root / "covers" / "book.webp", root / "private" / "users" / "user.webp", root / "reports" / "summary.pdf"]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test media")
    (root / "private" / "users" / "unrelated.webp").write_bytes(b"do not include")
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE books (cover_image TEXT)")
        db.execute("CREATE TABLE users (photo_image TEXT)")
        db.execute("CREATE TABLE report_jobs (file_path TEXT)")
        db.execute("INSERT INTO books VALUES ('/files/covers/book.webp')")
        db.execute("INSERT INTO users VALUES ('private/users/user.webp')")
        db.execute("INSERT INTO report_jobs VALUES ('generated/reports/summary.pdf')")

    output = bundle(source, root, tmp_path / "backups")
    with zipfile.ZipFile(output) as archive:
        assert set(archive.namelist()) == {
            "generated/covers/book.webp",
            "generated/private/users/user.webp",
            "generated/reports/summary.pdf",
        }


def test_missing_referenced_file_refuses_bundle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE books (cover_image TEXT)")
        db.execute("CREATE TABLE users (photo_image TEXT)")
        db.execute("CREATE TABLE report_jobs (file_path TEXT)")
        db.execute("INSERT INTO books VALUES ('/files/covers/missing.webp')")
    with pytest.raises(FileNotFoundError, match="referenced media"):
        bundle(source, tmp_path / "generated", tmp_path / "backups")
    assert not list((tmp_path / "backups").glob("*.zip"))
