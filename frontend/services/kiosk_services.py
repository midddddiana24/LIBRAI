"""Shared Flet service controls for the kiosk session.

Flet 0.86 desktop clients only register a service's invoke-method listener
when the service is part of the page's root view services list BEFORE the
first client sync. Services appended to ``page.overlay`` after that point
mount as controls but never answer method calls — every recorder, picker,
and audio call times out after 10 seconds.

Additionally, the ``record`` Windows plugin 7.1.1 shipped in the 0.86.5
desktop client never emits ``on_stream`` PCM chunks, while file-based
recording works. The kiosk therefore uses one shared AudioRecorder in
file mode, one shared FilePicker, and a pool of pre-created Audio players
for spoken replies.

This module must be imported and ``attach(page, web)`` called from
``app.main()`` BEFORE the first view is rendered.
"""

from __future__ import annotations

import asyncio

import flet as ft
import flet_audio_recorder as far
from flet_audio import Audio

# Audio players must exist before the first client sync, and their src is
# swapped per spoken reply (swapping works, but the client needs a moment
# to load the new source before play()).
AUDIO_PLAYER_POOL_SIZE = 2

# Named file pickers, one per purpose. Each purpose gets its own picker so
# upload event handlers never collide; all are created before the first
# client sync. Purposes are created lazily by name for tests/smoke routes,
# which build pages without app.main() running first.
_PICKER_PURPOSES = ("qr_photo", "csv_import", "book_cover", "user_photo")


def _ensure_pickers(page: ft.Page, services: dict[str, object]) -> None:
    pickers: dict[str, ft.FilePicker] = services.setdefault("pickers", {})
    for purpose in _PICKER_PURPOSES:
        if purpose not in pickers:
            picker = ft.FilePicker(on_upload=None)
            pickers[purpose] = picker
            page.services.append(picker)
    services.setdefault("picker", pickers["qr_photo"])


def get_named_picker(page: ft.Page, purpose: str) -> ft.FilePicker:
    """Return the shared FilePicker for a purpose, attached before sync."""
    services = get_services(page)
    pickers = services.setdefault("pickers", {})
    if purpose not in pickers:
        _ensure_pickers(page, services)
    return pickers[purpose]


def attach(page: ft.Page, web: bool) -> None:
    """Create and mount the shared kiosk services exactly once per session.

    Safe to call on every route rebuild: the services are stored on the
    page and reused.
    """
    if getattr(page, "_librai_services_attached", False):
        return

    services: dict[str, object] = {"picker": None, "recorder": None, "audio": []}

    # One FilePicker per purpose, all mounted before the first client sync.
    _ensure_pickers(page, services)

    if not web:
        # Shared microphone service, used in file-recording mode by the
        # hands-free header and the assistant page.
        services["recorder"] = far.AudioRecorder(
            configuration=far.AudioRecorderConfiguration(
                encoder=far.AudioEncoder.PCM16BITS,
                channels=1,
                sample_rate=16000,
                suppress_noise=True,
                cancel_echo=True,
                auto_gain=True,
            ),
        )
        page.services.append(services["recorder"])

        # Pre-created audio players for spoken replies. A silent 0.05 s WAV
        # placeholder keeps the player initialised; src is swapped per use.
        placeholder = (
            "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA="
        )
        pool: list[Audio] = []
        for _ in range(AUDIO_PLAYER_POOL_SIZE):
            player = Audio(src=placeholder, autoplay=False)
            page.services.append(player)
            pool.append(player)
        services["audio"] = pool

    setattr(page, "_librai_services", services)
    setattr(page, "_librai_services_attached", True)


def get_services(page: ft.Page) -> dict[str, object]:
    """Return the shared services dict, attaching lazily if a route was
    built before app.main() ran (e.g. tests and smoke harnesses)."""
    services = getattr(page, "_librai_services", None)
    if services is None:
        attach(page, web=bool(getattr(page, "web", False)))
        services = getattr(page, "_librai_services")
    return services


def get_recorder(page: ft.Page):
    """Shared AudioRecorder service, or None in web builds."""
    return get_services(page).get("recorder")


def get_picker(page: ft.Page):
    """Shared QR-photo FilePicker service."""
    return get_named_picker(page, "qr_photo")


async def speak(page: ft.Page, player: Audio, base64_audio: str) -> bool:
    """Play one spoken reply on a pre-created Audio service.

    The 0.86.5 desktop client needs a short settle time between swapping
    ``src`` and calling ``play()`` — an immediate play times out because
    the client has not finished loading the new source. Returns True when
    playback was started.
    """
    try:
        await player.release()
    except Exception:
        pass
    player.src = f"data:audio/mp3;base64,{base64_audio}"
    try:
        page.update()
    except AssertionError:
        pass
    await asyncio.sleep(1.0)
    try:
        await player.play()
        return True
    except Exception:
        return False
