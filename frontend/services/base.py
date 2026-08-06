"""Shared service fallback utilities."""

from core.config import settings
from core.constants import RequestState
from services.api_client import ApiResult


def fallback(result: ApiResult, data, message: str = "") -> ApiResult:
    if result.ok or not settings.use_mock_fallback or result.error_kind not in {
        RequestState.NETWORK_ERROR, RequestState.SERVER_ERROR
    }:
        return result
    mocked = ApiResult.success(data, is_mock=True)
    mocked.message = message
    return mocked
