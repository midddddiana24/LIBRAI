from __future__ import annotations

from types import SimpleNamespace

from backend.ai import gemini_client as module
from backend.ai.gemini_client import GeminiClient


def test_tokenrouter_glm_response_is_converted_to_existing_ranking_contract(monkeypatch):
    class FakeCompletions:
        def create(self, **_kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='{"message":"Found it.","recommendations":[{"book_id":1,"reason":"Matches Python."}]}'))]
            )

    class FakeOpenAI:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(module, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(module, "settings", SimpleNamespace(
        tokenrouter_api_key="test-token",
        tokenrouter_model="z-ai/glm-5.3-free",
        tokenrouter_base_url="https://api.tokenrouter.com/v1",
        gemini_api_key=None,
        gemini_timeout_seconds=5,
    ))

    result = GeminiClient().rank("Python books", [{"id": 1, "title": "Python", "author": "Author"}])

    assert result is not None
    assert result.message == "Found it."
    assert result.recommendations[0].book_id == 1


def test_failed_tokenrouter_tries_configured_gemini(monkeypatch):
    monkeypatch.setattr(module, "settings", SimpleNamespace(
        tokenrouter_api_key="rejected-test-key", gemini_api_key="test-gemini-key",
        gemini_model="test-model", gemini_timeout_seconds=5,
        gemini_retry_count=0, gemini_cache_seconds=30,
    ))
    client = GeminiClient()
    monkeypatch.setattr(client, "_rank_tokenrouter", lambda *_args: None)

    def fake_post(url, **kwargs):
        assert "test-model" in url
        assert kwargs["headers"]["x-goog-api-key"] == "test-gemini-key"
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {
            "candidates": [{"content": {"parts": [{"text":
                '{"message":"Gemini found it.","recommendations":[{"book_id":1,"reason":"Matches Python."}]}'
            }]}}]
        }, status_code=200)

    monkeypatch.setattr(module.httpx, "post", fake_post)
    result = client.rank("Python", [{"id": 1, "title": "Python", "author": "Author"}])
    assert result is not None and result.message == "Gemini found it."
    assert result.recommendations[0].book_id == 1
