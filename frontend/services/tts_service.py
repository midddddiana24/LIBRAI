"""Generate short spoken kiosk responses for tablet playback."""

from __future__ import annotations

import base64
from io import BytesIO

from gtts import gTTS


class TTSService:
    def synthesize_base64(self, text: str) -> str | None:
        phrase = str(text or "").strip()
        if not phrase:
            return None
        buffer = BytesIO()
        gTTS(text=phrase, lang="en", slow=False).write_to_fp(buffer)
        return base64.b64encode(buffer.getvalue()).decode("ascii")


tts_service = TTSService()
