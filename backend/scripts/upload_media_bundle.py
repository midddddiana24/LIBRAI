"""Upload a private LIBRAI media bundle to S3-compatible object storage.

The bucket must exist and be private. MEDIA_BUCKET, AWS_ENDPOINT_URL_S3,
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION come from environment
variables. Do not put the bundle, credentials, or command transcripts in Git.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path, PurePosixPath

from botocore.exceptions import ClientError

from backend.services.object_storage import _client
import os


def upload(bundle: Path) -> int:
    client = _client()
    bucket = os.environ["MEDIA_BUCKET"]
    with zipfile.ZipFile(bundle) as archive:
        files = [info for info in archive.infolist() if not info.is_dir()]
        for info in files:
            key = PurePosixPath(info.filename)
            if key.parts[:2] not in {("generated", "covers"), ("generated", "reports"), ("generated", "private")} or ".." in key.parts:
                raise ValueError("Media bundle contains an unexpected path; nothing was uploaded.")
            if key.parts[:2] == ("generated", "private") and key.parts[:3] != ("generated", "private", "users"):
                raise ValueError("Media bundle contains an unexpected private path; nothing was uploaded.")
        for info in files:
            key = info.filename
            try:
                client.head_object(Bucket=bucket, Key=key)
            except ClientError as exc:
                if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 404:
                    raise
            else:
                raise ValueError("Target bucket already contains a bundled file; stopped before overwriting it.")
        for info in files:
            key = info.filename
            suffix = Path(key).suffix.lower()
            media_type = {".webp": "image/webp", ".pdf": "application/pdf", ".csv": "text/csv", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}.get(suffix, "application/octet-stream")
            with archive.open(info) as source:
                client.put_object(Bucket=bucket, Key=key, Body=source.read(), ContentType=media_type)
    return len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media-bundle", required=True, type=Path)
    args = parser.parse_args()
    if not args.media_bundle.is_file():
        raise SystemExit("Media bundle was not found.")
    try:
        count = upload(args.media_bundle)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    except ClientError:
        raise SystemExit("Object storage request failed; check bucket permissions and credentials.") from None
    print(f"MEDIA_UPLOAD_COMPLETE files={count}")


if __name__ == "__main__":
    main()
