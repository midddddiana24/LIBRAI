import sqlite3

from backend.scripts.backup_sqlite import backup


def test_backup_includes_uncheckpointed_wal_rows(tmp_path):
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA wal_autocheckpoint=0")
        db.execute("CREATE TABLE records (value TEXT NOT NULL)")
        db.execute("INSERT INTO records (value) VALUES ('existing record')")
        db.commit()
        assert (tmp_path / "source.db-wal").exists()

        result = backup(f"sqlite:///{source}", tmp_path / "backups")
        with sqlite3.connect(result) as saved:
            assert saved.execute("SELECT value FROM records").fetchall() == [("existing record",)]
            assert saved.execute("PRAGMA integrity_check").fetchone() == ("ok",)
