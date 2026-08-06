"""Validated image processing and owned media-file lifecycle."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import secrets

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError

from backend.core.config import settings


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MEDIA_ROOT = Path("generated")


def store_image(content: bytes, content_type: str | None, kind: str, entity_id: int, old_value: str | None = None) -> str:
    """Validate, strip metadata, resize, and persist a normalized WebP image."""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(415, "Image must be JPEG, PNG, or WebP.")
    if not content:
        raise HTTPException(422, "The selected image is empty.")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(413, "Image is too large.")
    try:
        image = Image.open(BytesIO(content))
        image.verify()
        image = Image.open(BytesIO(content))
        if image.width * image.height > 36_000_000:
            raise HTTPException(422, "Image dimensions are too large.")
        image.thumbnail((1600, 1600) if kind == "covers" else (800, 800))
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(422, "The file is not a valid image.") from exc

    private = kind == "users"
    directory = MEDIA_ROOT / ("private/users" if private else "covers")
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{kind[:-1]}-{entity_id}-{secrets.token_hex(10)}.webp"
    path = directory / name
    image.save(path, format="WEBP", quality=86, method=6)
    _remove_owned(old_value)
    return f"private/users/{name}" if private else f"/files/covers/{name}"


def private_user_photo_path(stored_value: str | None) -> Path:
    if not stored_value or not stored_value.startswith("private/users/"):
        raise HTTPException(404, "User photo not found.")
    root = (MEDIA_ROOT / "private/users").resolve()
    path = (MEDIA_ROOT / stored_value).resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(404, "User photo not found.")
    return path


def _remove_owned(stored_value: str | None) -> None:
    if not stored_value:
        return
    relative = stored_value.removeprefix("/files/")
    candidate = (MEDIA_ROOT / relative).resolve()
    allowed_roots = [(MEDIA_ROOT / "covers").resolve(), (MEDIA_ROOT / "private/users").resolve()]
    if any(root in candidate.parents for root in allowed_roots) and candidate.is_file():
        candidate.unlink()
