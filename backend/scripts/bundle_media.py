"""Bundle media referenced by a SQLite backup for the Render persistent disk."""

from __future__ import annotations

import argparse
import sqlite3
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def bundle(backup_path: Path, media_root: Path = Path("generated"), output_dir: Path = Path("backups")) -> Path:
    backup_path = backup_path.resolve()
    root = media_root.resolve()
    if not backup_path.is_file():
        raise FileNotFoundError(backup_path)

    relative_paths: set[Path] = set()
    with closing(sqlite3.connect(f"file:{backup_path.as_posix()}?mode=ro", uri=True)) as db:
        for (value,) in db.execute("SELECT cover_image FROM books WHERE cover_image IS NOT NULL"):
            if not value.startswith("/files/covers/"):
                raise ValueError("A book has an unexpected cover path.")
            relative_paths.add(Path("covers") / value.removeprefix("/files/covers/"))
        for (value,) in db.execute("SELECT photo_image FROM users WHERE photo_image IS NOT NULL"):
            if not value.startswith("private/users/"):
                raise ValueError("A user has an unexpected photo path.")
            relative_paths.add(Path(value))
        for (value,) in db.execute("SELECT file_path FROM report_jobs WHERE file_path IS NOT NULL"):
            report = Path(value).resolve()
            if not report.is_relative_to(root) or report == root or report.relative_to(root).parts[0] != "reports":
                raise ValueError("A report has an unexpected file path.")
            relative_paths.add(report.relative_to(root))

    files: list[tuple[Path, Path]] = []
    for relative in sorted(relative_paths):
        if relative.parts[:1] == ("covers",):
            allowed = root / "covers"
        elif relative.parts[:2] == ("private", "users"):
            allowed = root / "private" / "users"
        elif relative.parts[:1] == ("reports",):
            allowed = root / "reports"
        else:
            raise ValueError("A referenced media path is outside its expected directory.")
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(allowed.resolve()) or not candidate.is_file():
            raise FileNotFoundError(f"A referenced media file is missing or outside {root}.")
        files.append((candidate, candidate.relative_to(root)))

    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"librai-media-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}.zip"
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, relative in files:
            archive.write(source, arcname=(Path("generated") / relative).as_posix())
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite-backup", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = bundle(args.sqlite_backup)
    except (FileNotFoundError, ValueError, sqlite3.Error) as exc:
        raise SystemExit(str(exc)) from None
    print(f"MEDIA_BUNDLE_CREATED {result}")


if __name__ == "__main__":
    main()
