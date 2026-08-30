"""Small dependency-free voice activity gate for streamed PCM16 audio.

It is intentionally conservative: it only ends a recording after speech has
started and a short quiet tail is detected. This keeps browser voice commands
responsive without requiring a heavyweight ML runtime on the kiosk.
"""

from __future__ import annotations

from array import array


class VoiceActivityDetector:
    def __init__(self, sample_rate: int = 16_000, silence_ms: int = 1_200, threshold: int = 450) -> None:
        self.sample_rate = sample_rate
        self.silence_ms = silence_ms
        self.threshold = threshold
        self.speech_started = False
        self._quiet_ms = 0

    def reset(self) -> None:
        self.speech_started = False
        self._quiet_ms = 0

    def accept(self, chunk: bytes) -> bool:
        """Accept one PCM16 chunk and return whether recording should finish."""
        if not chunk or len(chunk) < 2:
            return False
        samples = array("h")
        samples.frombytes(chunk[: len(chunk) - (len(chunk) % 2)])
        if not samples:
            return False
        rms = int((sum(sample * sample for sample in samples) / len(samples)) ** 0.5)
        duration_ms = max(1, round(len(samples) * 1000 / self.sample_rate))
        if rms >= self.threshold:
            self.speech_started = True
            self._quiet_ms = 0
        elif self.speech_started:
            self._quiet_ms += duration_ms
        return self.speech_started and self._quiet_ms >= self.silence_ms
