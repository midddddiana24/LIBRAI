"""Keep Gemini credentials out of request URLs and routine HTTP logs."""

import logging
from types import SimpleNamespace

from backend.ai import gemini_client as module
from backend.ai.gemini_client import GeminiClient


def test_gemini_requests_send_key_in_header(monkeypatch):
    secret = "test-gemini-secret"
    requests = []

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            if len(requests) == 1:
                return {"candidates": [{"content": {"parts": [{"text": '{"message":"Found it.","recommendations":[{"book_id":1,"reason":"Matches."}]}' }]}}]}
            return {"candidates": [{"content": {"parts": [{"text": "Find books about Python programming."}]}}]}

    def fake_post(url, **kwargs):
        requests.append((url, kwargs))
        return Response()

    monkeypatch.setattr(module.httpx, "post", fake_post)
    monkeypatch.setattr(module, "settings", SimpleNamespace(
        gemini_api_key=secret,
        gemini_model="test-model",
        gemini_retry_count=0,
        gemini_timeout_seconds=5,
        gemini_cache_seconds=30,
        tokenrouter_api_key=None,
    ))

    client = GeminiClient()
    ranked = client.rank("Python", [{"id": 1, "title": "Python", "author": "Author"}])
    transcript = client.transcribe(b"test audio", "audio/wav")

    assert ranked is not None
    assert transcript == "Find books about Python programming."
    assert len(requests) == 2
    for url, kwargs in requests:
        assert secret not in url
        assert kwargs["headers"]["x-goog-api-key"] == secret
        assert "params" not in kwargs
    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
