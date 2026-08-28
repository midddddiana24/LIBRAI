"""
LIBRAI - Centralized API client.

Every backend call in the frontend MUST go through this module (or a
service that wraps it). No page/component should use `requests`
directly.

Provides:
- ApiResult: a uniform envelope (ok, status, data, error_kind, message)
  so pages can render loading/success/error states consistently.
- ApiClient: thin wrapper around `requests` with timeout, JSON
  handling, and error classification.
- ApiError / error kinds mapped to core.constants.RequestState so the
  UI layer can react appropriately (validation vs auth vs network...).
"""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlsplit
from pathlib import Path
import mimetypes

import requests

from core.config import settings
from core.constants import RequestState


@dataclass
class ApiResult:
    ok: bool
    status_code: Optional[int] = None
    data: Any = None
    error_kind: str = RequestState.IDLE
    message: str = ""
    is_mock: bool = False

    @staticmethod
    def success(data: Any, status_code: int = 200, is_mock: bool = False) -> "ApiResult":
        return ApiResult(ok=True, status_code=status_code, data=data, is_mock=is_mock)

    @staticmethod
    def failure(kind: str, message: str, status_code: Optional[int] = None) -> "ApiResult":
        return ApiResult(ok=False, status_code=status_code, error_kind=kind, message=message)


def _classify_status(status_code: int) -> str:
    if status_code == 401:
        return RequestState.AUTH_ERROR
    if status_code == 403:
        return RequestState.PERMISSION_ERROR
    if status_code in {400, 404, 409, 422, 429}:
        return RequestState.VALIDATION_ERROR
    if status_code >= 500:
        return RequestState.SERVER_ERROR
    return RequestState.SERVER_ERROR


class ApiClient:
    """Thin, testable HTTP wrapper. One instance is shared app-wide via
    `api_client` below. Services (book_service, borrowing_service, ...)
    call `.get/.post/.put/.delete` and receive an `ApiResult`.
    """

    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout or settings.api_timeout_seconds
        # Flet preserves a context per connected page/session. A ContextVar
        # keeps concurrent browser sessions from overwriting each other's
        # administrator bearer token while retaining one shared API client.
        self._auth_token: ContextVar[Optional[str]] = ContextVar(
            f"librai_auth_token_{id(self)}", default=None
        )

    def set_auth_token(self, token: Optional[str]) -> None:
        """Called by auth_service after login / on logout."""
        self._auth_token.set(token)

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        auth_token = self._auth_token.get()
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def resolve_url(self, path: str) -> str:
        """Resolve an API-relative URL returned by the backend."""
        if path.startswith(("http://", "https://")):
            return path
        if path.startswith(("/api/", "/files/")):
            parsed = urlsplit(self.base_url)
            return f"{parsed.scheme}://{parsed.netloc}{path}"
        return self._url(path)

    def health(self) -> ApiResult:
        """Check the server-level health endpoint outside the API prefix."""
        parsed = urlsplit(self.base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        try:
            response = requests.get(f"{origin}/health", timeout=min(self.timeout, 3))
            if 200 <= response.status_code < 300:
                return ApiResult.success(response.json() if response.content else {})
            return ApiResult.failure(RequestState.SERVER_ERROR, "The LIBRAI server health check failed.", response.status_code)
        except requests.exceptions.RequestException:
            return ApiResult.failure(RequestState.NETWORK_ERROR, "Could not reach the LIBRAI server.")

    def _request(self, method: str, path: str, **kwargs) -> ApiResult:
        url = self._url(path)
        headers = kwargs.pop("headers", self._headers())
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.exceptions.Timeout:
            return ApiResult.failure(RequestState.NETWORK_ERROR, "The request timed out. Please check your connection.")
        except requests.exceptions.ConnectionError:
            return ApiResult.failure(RequestState.NETWORK_ERROR, "Could not reach the LIBRAI server.")
        except requests.exceptions.RequestException as exc:  # pragma: no cover
            return ApiResult.failure(RequestState.NETWORK_ERROR, f"Network error: {exc}")

        try:
            payload = response.json() if response.content else None
        except ValueError:
            payload = None

        if 200 <= response.status_code < 300:
            data = payload if payload is not None else {}
            data = self._resolve_media_urls(data)
            if isinstance(data, (list, dict)) and len(data) == 0:
                return ApiResult(ok=True, status_code=response.status_code, data=data, error_kind=RequestState.EMPTY)
            return ApiResult.success(data, status_code=response.status_code)

        message = "Something went wrong."
        if isinstance(payload, dict):
            detail = payload.get("message") or payload.get("detail")
            if isinstance(detail, list):
                detail = "; ".join(str(item.get("msg", item)) if isinstance(item, dict) else str(item) for item in detail)
            if detail:
                message = str(detail)
        return ApiResult.failure(_classify_status(response.status_code), message, status_code=response.status_code)

    # Public verbs -------------------------------------------------
    def get(self, path: str, params: dict | None = None) -> ApiResult:
        return self._request("GET", path, params=params)

    def post(self, path: str, json_body: dict | None = None) -> ApiResult:
        return self._request("POST", path, json=json_body)

    def put(self, path: str, json_body: dict | None = None) -> ApiResult:
        return self._request("PUT", path, json=json_body)

    def delete(self, path: str, params: dict | None = None) -> ApiResult:
        return self._request("DELETE", path, params=params)

    def upload_file(self, path: str, file_path: str | Path, field_name: str = "file") -> ApiResult:
        """Upload one local file through the centralized authenticated client."""
        source = Path(file_path)
        if not source.is_file():
            message = "The audio recording is no longer available." if field_name == "audio" else "The selected image is no longer available."
            return ApiResult.failure(RequestState.VALIDATION_ERROR, message)
        headers = self._headers()
        headers.pop("Content-Type", None)
        media_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        try:
            with source.open("rb") as handle:
                return self._request(
                    "POST",
                    path,
                    headers=headers,
                    files={field_name: (source.name, handle, media_type)},
                )
        except OSError:
            message = "The audio recording could not be read." if field_name == "audio" else "The selected image could not be read."
            return ApiResult.failure(RequestState.VALIDATION_ERROR, message)

    def _resolve_media_urls(self, value: Any) -> Any:
        """Resolve API-relative image URLs so Flet requests them from FastAPI."""
        if isinstance(value, list):
            return [self._resolve_media_urls(item) for item in value]
        if isinstance(value, dict):
            resolved = {}
            for key, item in value.items():
                if key in {"cover_url", "cover_image", "photo_url"} and isinstance(item, str) and item.startswith("/"):
                    resolved[key] = self.resolve_url(item)
                else:
                    resolved[key] = self._resolve_media_urls(item)
            return resolved
        return value


# Shared singleton used across all services.
api_client = ApiClient()
