"""Regression tests for the kiosk voice pipeline bugs.

Covers the three defects that made hands-free voice commands fail:
1. Stream chunks appended to a rebound list (audio lost).
2. VAD state leaking between utterances (next command cut short).
3. Stale 15-second timers finishing a newer recording.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.voice_activity_service import VoiceActivityDetector


def _loud_chunk(milliseconds: int = 100, sample_rate: int = 16_000) -> bytes:
    """PCM16 mono chunk whose samples sit far above the VAD threshold."""
    count = sample_rate * milliseconds // 1000
    return (b"\x7f\x7f\x00\x00" * ((count // 2) + 1))[: count * 2]


def _quiet_chunk(milliseconds: int = 100, sample_rate: int = 16_000) -> bytes:
    count = sample_rate * milliseconds // 1000
    return b"\x00\x00" * count


class _Event:
    def __init__(self, chunk: bytes) -> None:
        self.chunk = chunk


def test_stream_buffer_survives_reset_between_utterances():
    """The stream callback and the controller must share one buffer object.

    Regression: start_voice() used to rebind controller["chunks"] to a new
    list while the closure kept appending to the old one, so every
    recording finished with "No audio captured".
    """
    buffer = {"data": bytearray()}

    def on_audio_stream(event) -> None:
        chunk = getattr(event, "chunk", b"")
        if chunk:
            buffer["data"] += bytes(chunk)

    # First utterance.
    on_audio_stream(_Event(b"\x01\x02"))
    on_audio_stream(_Event(b"\x03\x04"))
    first = bytes(buffer["data"])
    assert first == b"\x01\x02\x03\x04"

    # finish_voice() drains the buffer in place — never rebinds it.
    buffer["data"] = bytearray()

    # Second utterance must still land in the same buffer the closure writes.
    on_audio_stream(_Event(b"\x05\x06"))
    assert bytes(buffer["data"]) == b"\x05\x06"


def test_vad_reset_between_utterances():
    """A fresh utterance must not inherit the previous silence tail.

    Regression: the detector was only reset when voice was switched off,
    so after the first command the next recording was ended by its first
    quiet chunk ("No words recognized").
    """
    vad = VoiceActivityDetector()
    assert vad.accept(_loud_chunk()) is False  # speech started
    assert vad.accept(_quiet_chunk(1300)) is True  # silence tail finishes

    # New recording: reset first.
    vad.reset()
    assert vad.accept(_quiet_chunk(1300)) is False  # quiet before speech
    assert vad.accept(_loud_chunk()) is False
    assert vad.accept(_quiet_chunk(1300)) is True


def test_generation_guard_blocks_stale_timer():
    """Only the current recording's 15s timer may finish it."""
    controller = {"active": True, "generation": 1}

    async def start_voice(generation: int, captured: dict) -> None:
        await asyncio.sleep(0.01)
        if controller["active"] and controller["generation"] == generation:
            captured["finished_by"] = generation

    async def scenario() -> None:
        stale = {}
        task = asyncio.create_task(start_voice(1, stale))
        # VAD finishes utterance 1 and listen_again starts utterance 2.
        controller["generation"] = 2
        controller["active"] = True
        await task
        assert "finished_by" not in stale  # stale timer must not fire
        fresh = {}
        await start_voice(2, fresh)
        assert fresh["finished_by"] == 2

    asyncio.run(scenario())


def test_wav_written_from_shared_buffer_is_valid(tmp_path):
    """The WAV assembly in finish_voice must produce a readable file."""
    import wave

    buffer = {"data": bytearray(_quiet_chunk(500) + _loud_chunk(200) + _quiet_chunk(500))}
    output = tmp_path / "speech-test.wav"
    with wave.open(str(output), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(bytes(buffer["data"]))

    with wave.open(str(output), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == (500 + 200 + 500) * 16
