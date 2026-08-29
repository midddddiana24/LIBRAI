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
