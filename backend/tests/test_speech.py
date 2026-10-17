import asyncio

import pytest

from backend.ai.gemini_client import gemini_client
from backend.core.config import settings
from backend.main import requests_by_ip


def test_speech_requires_audio_and_configured_provider(client):
    assert client.post('/api/v1/speech/transcribe', files={'audio': ('bad.txt', b'text', 'text/plain')}).status_code == 415
    assert client.post('/api/v1/speech/transcribe', files={'audio': ('empty.wav', b'', 'audio/wav')}).status_code == 422
    assert client.post('/api/v1/speech/transcribe', files={'audio': ('test.wav', b'audio', 'audio/wav')}).status_code == 503


def test_speech_normalizes_wav_without_blocking_event_loop(client, monkeypatch):
    monkeypatch.setattr(settings, 'gemini_api_key', 'fake-test-key')

    def transcribe(content, mime_type, language):
        assert language == 'fil'
        assert content == b'test-audio' and mime_type == 'audio/wav'
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()
        return 'Find Python books.'

    monkeypatch.setattr(gemini_client, 'transcribe', transcribe)
    response = client.post('/api/v1/speech/transcribe', data={'language': 'fil'}, files={'audio': ('test.wav', b'test-audio', 'audio/x-wav')})
    assert response.status_code == 200 and response.json() == {'text': 'Find Python books.'}


@pytest.mark.parametrize('path,body,first_status', [
    ('/api/v1/ai/recommend', {'kind': 'popular'}, 200),
    ('/api/v1/speech/transcribe', {}, 422),
])
def test_public_ai_routes_have_request_limits(client, monkeypatch, path, body, first_status):
    monkeypatch.setattr(settings, 'rate_limit_requests_per_window', 1)
    requests_by_ip.clear()
    try:
        assert client.post(path, json=body).status_code == first_status
        limited = client.post(path, json=body)
        assert limited.status_code == 429 and 'Retry-After' in limited.headers
    finally:
        requests_by_ip.clear()


def test_speech_rejects_unsupported_language(client):
    response = client.post('/api/v1/speech/transcribe', data={'language': 'invented'}, files={'audio': ('test.wav', b'audio', 'audio/wav')})
    assert response.status_code == 422
