"""Optional S3-compatible persistence for media on diskless free web services."""

from __future__ import annotations

from pathlib import Path

from botocore.config import Config
from botocore.exceptions import ClientError
import boto3
from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from backend.core.config import settings


def enabled() -> bool:
    return bool(settings.media_bucket)


def _client():
    required = {
        "MEDIA_BUCKET": settings.media_bucket,
        "AWS_ENDPOINT_URL_S3": settings.aws_endpoint_url_s3,
        "AWS_ACCESS_KEY_ID": settings.aws_access_key_id,
        "AWS_SECRET_ACCESS_KEY": settings.aws_secret_access_key,
        "AWS_REGION": settings.aws_region,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError("Object storage is not fully configured: " + ", ".join(missing))
    return boto3.client(
        "s3",
        endpoint_url=settings.aws_endpoint_url_s3,
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        config=Config(s3={"addressing_style": "path"}),
    )


def put(key: str, content: bytes, media_type: str) -> None:
    _client().put_object(Bucket=settings.media_bucket, Key=key, Body=content, ContentType=media_type)


def put_file(path: Path) -> str:
    """Persist a generated report; return its existing relative database path."""
    if enabled():
        suffix_types = {".pdf": "application/pdf", ".csv": "text/csv", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        put(path.as_posix(), path.read_bytes(), suffix_types.get(path.suffix.lower(), "application/octet-stream"))
        path.unlink()
    return str(path)


def delete(key: str) -> None:
    _client().delete_object(Bucket=settings.media_bucket, Key=key)


def media_response(path: str | Path, *, media_type: str | None = None, filename: str | None = None, headers: dict[str, str] | None = None):
    """Read private files through the API; never expose a public bucket URL."""
    key = Path(path).as_posix()
    if not enabled():
        if not Path(path).is_file():
            raise HTTPException(404, "File not found.")
        return FileResponse(path, media_type=media_type, filename=filename, headers=headers)
    if not key.startswith("generated/") or ".." in Path(key).parts:
        raise HTTPException(404, "File not found.")
    try:
        obj = _client().get_object(Bucket=settings.media_bucket, Key=key)
        body = obj["Body"].read()
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchKey", "404", "NotFound"}:
            raise HTTPException(404, "File not found.") from None
        raise
    result_headers = dict(headers or {})
    if filename:
        result_headers["Content-Disposition"] = f'attachment; filename="{Path(filename).name}"'
    return Response(body, media_type=media_type or obj.get("ContentType") or "application/octet-stream", headers=result_headers)
