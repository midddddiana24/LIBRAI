"""
LIBRAI - Environment/configuration loader.

All environment-dependent values (API base URL, timeouts, feature flags)
live here. Nothing else in the frontend should read os.environ directly.

Configure via a `.env` file in `frontend/` (see `.env.example`) or real
environment variables. Environment variables always take precedence.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    # Optional dependency; if python-dotenv isn't installed we silently
    # fall back to real environment variables only.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    school_name: str = os.getenv("LIBRAI_SCHOOL_NAME", "Your School Name")
    library_name: str = os.getenv("LIBRAI_LIBRARY_NAME", "School Learning Resource Center")

    # Base URL of the Codex-owned FastAPI backend.
    api_base_url: str = os.getenv("LIBRAI_API_BASE_URL", "http://127.0.0.1:8000/api/v1")

    # Request timeout (seconds) for all outgoing API calls.
    api_timeout_seconds: int = _get_int("LIBRAI_API_TIMEOUT_SECONDS", 10)

    # When True, services fall back to documented mock responses if a
    # backend endpoint is unreachable or not yet implemented by Codex.
    # This should be turned OFF for the final deployed/demo build once
    # the backend contract is fully implemented.
    use_mock_fallback: bool = _get_bool("LIBRAI_USE_MOCK_FALLBACK", False)

    # Kiosk vs. staff/admin mode toggle (affects default route).
    default_mode: str = os.getenv("LIBRAI_DEFAULT_MODE", "kiosk")

    # Window sizing hints for desktop/kiosk deployment (Flet).
    window_width: int = _get_int("LIBRAI_WINDOW_WIDTH", 1366)
    window_height: int = _get_int("LIBRAI_WINDOW_HEIGHT", 768)
    fullscreen: bool = _get_bool("LIBRAI_FULLSCREEN", False)

    # Local kiosk laptop camera opened by the Python frontend process.
    camera_index: int = _get_int("LIBRAI_CAMERA_INDEX", 0)
    frontend_upload_directory: Path = Path(os.getenv("LIBRAI_FRONTEND_UPLOAD_DIRECTORY", "generated/frontend_uploads")).resolve()


settings = Settings()
