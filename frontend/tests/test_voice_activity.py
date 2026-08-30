from services.voice_activity_service import VoiceActivityDetector


def test_quiet_audio_does_not_finish_before_speech():
    vad = VoiceActivityDetector(silence_ms=100)
    assert not vad.accept(b"\0\0" * 1600)


def test_detector_finishes_after_speech_and_quiet_tail():
    vad = VoiceActivityDetector(silence_ms=100, threshold=10)
    assert not vad.accept((100).to_bytes(2, "little", signed=True) * 1600)
    assert vad.accept(b"\0\0" * 1600)
