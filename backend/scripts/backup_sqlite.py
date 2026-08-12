"""Create a consistent SQLite backup without modifying the live database."""
from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
from backend.core.config import settings

def backup() -> Path:
    if not settings.database_url.startswith("sqlite:///"):
        raise RuntimeError("This utility supports SQLite only. Use pg_dump for PostgreSQL deployments.")
    source = Path(settings.database_url.removeprefix("sqlite:///"))
    if not source.exists():
        raise FileNotFoundError(source)
    target_dir = Path("backups")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"librai-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    shutil.copy2(source, target)
    return target

if __name__ == "__main__":
    print(f"SQLITE_BACKUP_CREATED {backup()}")
