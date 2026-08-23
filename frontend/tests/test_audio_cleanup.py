from __future__ import annotations

import os
import sys
import time
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kiosk.ai_assistant_page import cleanup_stale_recordings


def test_cleanup_removes_only_old_speech_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kiosk.ai_assistant_page.settings",
        SimpleNamespace(frontend_upload_directory=tmp_path),
    )
    old_file = tmp_path / "speech-old.wav"
    fresh_file = tmp_path / "speech-fresh.wav"
    unrelated = tmp_path / "image.png"
    for path in (old_file, fresh_file, unrelated):
        path.write_bytes(b"test")
    old_time = time.time() - 7200
    os.utime(old_file, (old_time, old_time))

    cleanup_stale_recordings(max_age_seconds=3600)

    assert not old_file.exists()
    assert fresh_file.exists()
    assert unrelated.exists()
