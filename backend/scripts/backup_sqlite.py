"""Create a consistent local SQLite backup, including uncheckpointed WAL data."""
from __future__ import annotations
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from backend.core.config import settings

def backup(database_url: str | None = None, target_dir: Path | None = None) -> Path:
    database_url = database_url or settings.database_url
    if not database_url.startswith("sqlite:///"):
        raise RuntimeError("This utility supports SQLite only. Use pg_dump for PostgreSQL deployments.")
    source = Path(database_url.removeprefix("sqlite:///"))
    if not source.exists():
        raise FileNotFoundError(source)
    target_dir = target_dir or Path("backups")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"librai-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}.db"
    source_uri = f"file:{source.resolve().as_posix()}?mode=ro"
    with closing(sqlite3.connect(source_uri, uri=True)) as source_db:
        with closing(sqlite3.connect(target)) as target_db:
            source_db.backup(target_db)
    return target

if __name__ == "__main__":
    print(f"SQLITE_BACKUP_CREATED {backup()}")
