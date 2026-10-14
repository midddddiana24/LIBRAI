"""Copy a LIBRAI SQLite backup into an empty, migrated PostgreSQL database.

The source must be a completed SQLite backup, not the application's active DB.
The target must already have the same Alembic schema. The copy is one database
transaction and refuses to merge into a database that contains any app rows.
"""

from __future__ import annotations

import argparse
import getpass
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import DateTime, Engine, create_engine, func, inspect, select, text
from sqlalchemy.exc import SQLAlchemyError

from backend.core.database import Base
import backend.models  # noqa: F401 - registers all tables with Base.metadata


def copy_records(source_engine: Engine, target_engine: Engine) -> dict[str, int]:
    """Copy all model tables with their IDs, refusing schema drift or existing rows."""
    tables = Base.metadata.sorted_tables
    counts: dict[str, int] = {}
    with source_engine.connect() as source, target_engine.begin() as target:
        source_schema = inspect(source)
        target_schema = inspect(target)
        if not source_schema.has_table("alembic_version") or not target_schema.has_table("alembic_version"):
            raise ValueError("Both databases must have an Alembic-managed schema.")
        source_revision = source.scalar(text("SELECT version_num FROM alembic_version"))
        target_revision = target.scalar(text("SELECT version_num FROM alembic_version"))
        if not source_revision or source_revision != target_revision:
            raise ValueError("Source and target Alembic revisions differ; migrate both to the same version first.")

        for table in tables:
            name = table.name
            if not source_schema.has_table(name) or not target_schema.has_table(name):
                raise ValueError(f"Missing table: {name}.")
            expected = {column.name for column in table.columns}
            source_columns = {column["name"] for column in source_schema.get_columns(name)}
            target_columns = {column["name"] for column in target_schema.get_columns(name)}
            if source_columns != expected or target_columns != expected:
                raise ValueError(f"Schema columns differ for {name}; no data was copied.")
            if target.scalar(select(func.count()).select_from(table)):
                raise ValueError(f"Target table {name} already has records; no data was copied.")

        for table in tables:
            rows = source.execute(select(table)).mappings()
            count = 0
            while batch := rows.fetchmany(500):
                prepared = []
                for row in batch:
                    values = dict(row)
                    for column in table.columns:
                        value = values[column.name]
                        if isinstance(column.type, DateTime) and isinstance(value, datetime) and value.tzinfo is None:
                            values[column.name] = value.replace(tzinfo=timezone.utc)
                    prepared.append(values)
                target.execute(table.insert(), prepared)
                count += len(prepared)
            counts[table.name] = count
            if target.scalar(select(func.count()).select_from(table)) != count:
                raise ValueError(f"Target row count differs for {table.name}; copy was rolled back.")

        if target.dialect.name == "postgresql":
            for table in tables:
                for column in table.primary_key.columns:
                    if column.autoincrement is False:
                        continue
                    sequence = target.scalar(
                        text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
                        {"table_name": table.name, "column_name": column.name},
                    )
                    if sequence:
                        largest = target.scalar(select(func.max(column)))
                        target.execute(
                            text("SELECT setval(CAST(:sequence AS regclass), :value, :used)"),
                            {"sequence": sequence, "value": largest or 1, "used": largest is not None},
                        )
    return counts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite-backup", type=Path, required=True, help="Consistent backup made after resetting the local admin password")
    args = parser.parse_args(argv)
    source_path = args.sqlite_backup.resolve()
    if not source_path.is_file():
        raise SystemExit("SQLite backup file was not found.")
    with closing(sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)) as check:
        if check.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise SystemExit("SQLite backup failed its integrity check.")
    if not sys.stdin.isatty():
        raise SystemExit("An interactive terminal is required for the PostgreSQL URL.")
    target_url = getpass.getpass("PostgreSQL external URL (input hidden): ").strip()
    if target_url.startswith("postgres://"):
        target_url = "postgresql+psycopg://" + target_url.removeprefix("postgres://")
    elif target_url.startswith("postgresql://"):
        target_url = "postgresql+psycopg://" + target_url.removeprefix("postgresql://")
    if not target_url.startswith("postgresql+psycopg://"):
        raise SystemExit("Enter a PostgreSQL connection URL using the psycopg driver.")

    source_uri = f"file:{source_path.as_posix()}?mode=ro"
    source_engine = create_engine("sqlite://", creator=lambda: sqlite3.connect(source_uri, uri=True))
    try:
        target_engine = create_engine(target_url, pool_pre_ping=True)
    except (ValueError, SQLAlchemyError):
        source_engine.dispose()
        raise SystemExit("The PostgreSQL URL could not be parsed. Check its format and try again.") from None
    try:
        counts = copy_records(source_engine, target_engine)
    except (ValueError, SQLAlchemyError) as exc:
        # Database errors can contain credentials in their connection details.
        if isinstance(exc, ValueError):
            raise SystemExit(str(exc)) from None
        raise SystemExit("Database copy failed; verify the URL, network access, and migrated empty target. No app rows were committed.") from None
    finally:
        source_engine.dispose()
        target_engine.dispose()
    print("COPY_COMPLETE " + ", ".join(f"{name}={count}" for name, count in counts.items()))


if __name__ == "__main__":
    main()
