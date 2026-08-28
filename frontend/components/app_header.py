"""
LIBRAI – Kiosk App Header
=========================
Thin, refined top bar shown on every kiosk sub-page.
Reads from the design system — no hardcoded colors here.
"""

from __future__ import annotations
import asyncio
import uuid
from pathlib import Path
import flet as ft
import flet_audio_recorder as far

from components.brand_logo import BrandLogo
from core.config   import settings
from core.constants import APP_NAME, Routes
from core.state    import get_state
from core.theme    import Colors, Radius, Spacing
from services.api_client import api_client
from services.speech_service import speech_service
from services.voice_command_service import resolve_voice_command
from services.tts_service import tts_service


def AppHeader(
    page: ft.Page,
    title: str | None = None,
    show_back: bool = False,
    session_label: str | None = None,
    show_home: bool = True,
) -> ft.Container:
    state   = get_state(page)
    compact = (getattr(page, "width", None) or 1366) < 820
    health = api_client.health()
    health_data = health.data if health.ok and isinstance(health.data, dict) else {}
    health_ok = health.ok and health_data.get("status") == "healthy"
    health_label = "API ready · DB connected · Gemini ready" if health_ok else "Offline mode · reconnect required"
    health_color = Colors.SUCCESS if health_ok else Colors.ERROR

    # ── Left cluster ──────────────────────────────────────────
    left: list[ft.Control] = []

    if show_back:
        left.append(
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                icon_color=Colors.TEXT_PRIMARY,
                icon_size=20,
                tooltip="Go back",
                style=ft.ButtonStyle(enable_feedback=False,
                                     shape=ft.RoundedRectangleBorder(radius=Radius.SM)),
                on_click=lambda _e: page.go(Routes.HOME),
            )
        )

    # Logo mark
    left.append(
        ft.Row(
            spacing=Spacing.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                BrandLogo(52, 42),
                ft.Column(
                    spacing=0,
                    tight=True,
                    controls=[
                        ft.Text(APP_NAME, size=15, weight=ft.FontWeight.W_800,
                                color=Colors.TEXT_PRIMARY),
                        ft.Text(
                            settings.library_name,
                            size=10,
                            color=Colors.TEXT_SECONDARY,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                ),
            ],
        )
    )

    # Page title divider + label
    if title and not compact:
        left += [
            ft.Container(width=1, height=24, bgcolor=Colors.BORDER,
                         margin=ft.margin.symmetric(horizontal=4)),
            ft.Text(title, size=13, weight=ft.FontWeight.W_600,
                    color=Colors.TEXT_SECONDARY, max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS),
        ]

    # ── Right cluster ─────────────────────────────────────────
    right: list[ft.Control] = []

    voice_enabled = page.client_storage.get("librai_voice_enabled") == "true"
    controller = getattr(page, "_librai_voice_controller", None)
    if controller is None:
        recorder = far.AudioRecorder(suppress_noise=True, cancel_echo=True, auto_gain=True, sample_rate=16000)
        page.overlay.append(recorder)
        controller = {"recorder": recorder, "reply_audio": None, "active": False, "path": None, "button": None, "status": None, "status_value": "Ready"}
        setattr(page, "_librai_voice_controller", controller)

    voice_button: ft.FilledButton
    voice_status = ft.Text(controller.get("status_value", "Ready"), size=10, color=Colors.TEXT_SECONDARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    controller["status"] = voice_status

    def voice_is_enabled() -> bool:
        try:
            return page.client_storage.get("librai_voice_enabled") == "true"
        except (TimeoutError, RuntimeError):
            return False

    def set_voice_label(label: str, active: bool = False) -> None:
        voice_button.text = label
        voice_button.icon = ft.Icons.MIC_ROUNDED if active else ft.Icons.MIC_OFF_ROUNDED
        try:
            voice_button.update()
        except AssertionError:
            # The first auto-listen task can run before the new header has
            # been attached to the page during a route rebuild.
            pass

    def set_voice_status(value: str, color: str = Colors.TEXT_SECONDARY) -> None:
        controller["status_value"] = value
        voice_status.value = value
        voice_status.color = color
        try:
            voice_status.update()
        except AssertionError:
            pass

    def cleanup_voice_file(path: str | None) -> None:
        if not path:
            return
        candidate = Path(path).resolve()
        root = settings.frontend_upload_directory.resolve()
        if candidate.is_file() and root in candidate.parents:
            try:
                candidate.unlink()
            except OSError:
                pass

    async def listen_again() -> None:
        await asyncio.sleep(0.6)
        if voice_is_enabled() and not controller["active"]:
            await start_voice()

    async def speak_reply(reply: str) -> None:
        """Speak without delaying the kiosk navigation."""
        set_voice_status("Speaking", Colors.PRIMARY)
        try:
            audio = await asyncio.wait_for(
                asyncio.to_thread(tts_service.synthesize_base64, reply),
                timeout=3,
            )
            if audio:
                reply_audio = ft.Audio(src_base64=audio, autoplay=True)
                controller["reply_audio"] = reply_audio
                page.overlay.append(reply_audio)
                page.update()
                reply_audio.play()
                await asyncio.sleep(0.5)
            set_voice_status("Command completed", Colors.SUCCESS)
        except Exception:
            set_voice_status("Command completed (text only)", Colors.SUCCESS)

    async def finish_voice() -> None:
        if not controller["active"]:
            return
        controller["active"] = False
        set_voice_label("Processing…", active=True)
        set_voice_status("Processing", Colors.PRIMARY)
        path = await asyncio.to_thread(controller["recorder"].stop_recording)
        controller["path"] = path
        if not path:
            set_voice_label("Voice ON")
            set_voice_status("No speech captured", Colors.ERROR)
            return
        result = await asyncio.to_thread(speech_service.transcribe, str(path))
        cleanup_voice_file(str(path))
        if result.ok:
            spoken = str((result.data or {}).get("text", "")).strip()
            command = resolve_voice_command(spoken)
            reply = command.get("spoken_reply") or command.get("message")
            heard = spoken[:80] if spoken else "No words recognized"
            set_voice_status(f"Heard: {heard}", Colors.SUCCESS if spoken else Colors.ERROR)
            page.run_task(speak_reply, reply)
            if command["action"] == "navigate":
                page.go(command["route"])
            elif command["action"] in {"search", "search_available", "clear_search"}:
                page.client_storage.set("librai_pending_search", command.get("query", ""))
                page.client_storage.set("librai_pending_available_only", command["action"] == "search_available")
                page.go(Routes.SEARCH)
            elif command["action"] == "back":
                page.go(Routes.HOME)
        else:
            set_voice_status(f"Speech error: {result.message[:60]}", Colors.ERROR)
        set_voice_label("Voice ON")
        if voice_is_enabled():
            page.run_task(listen_again)

    async def stop_voice() -> None:
        try:
            page.client_storage.set("librai_voice_enabled", "false")
        except (TimeoutError, RuntimeError):
            pass
        if controller["active"]:
            controller["active"] = False
            path = await asyncio.to_thread(controller["recorder"].stop_recording)
            cleanup_voice_file(str(path) if path else None)
        set_voice_label("Voice OFF")

    async def start_voice() -> None:
        if controller["active"]:
            return
        settings.frontend_upload_directory.mkdir(parents=True, exist_ok=True)
        output = settings.frontend_upload_directory / f"speech-{uuid.uuid4().hex}.wav"
        try:
            started = await asyncio.to_thread(controller["recorder"].start_recording, str(output))
        except Exception:
            started = False
        if not started:
            set_voice_status("Microphone unavailable", Colors.ERROR)
            set_voice_label("Voice OFF")
            return
        controller["active"] = True
        controller["path"] = output
        set_voice_status("Listening", Colors.PRIMARY)
        set_voice_label("Listening…", active=True)
        await asyncio.sleep(6)
        if controller["active"]:
            await finish_voice()

    def toggle_voice(_event) -> None:
        enabled = voice_is_enabled()
        if enabled:
            try:
                page.client_storage.remove("librai_voice_mode")
            except (TimeoutError, RuntimeError):
                pass
            page.run_task(stop_voice)
            return
        try:
            page.client_storage.set("librai_voice_enabled", "true")
        except (TimeoutError, RuntimeError):
            return
        page.run_task(start_voice)

    voice_button = ft.FilledButton(
            "Voice ON" if voice_enabled else "Voice OFF",
            icon=ft.Icons.MIC_ROUNDED if voice_enabled else ft.Icons.MIC_OFF_ROUNDED,
            on_click=toggle_voice,
            style=ft.ButtonStyle(
                bgcolor=Colors.SUCCESS if voice_enabled else Colors.SURFACE_ALT,
                color=Colors.ON_PRIMARY if voice_enabled else Colors.TEXT_SECONDARY,
                shape=ft.RoundedRectangleBorder(radius=Radius.PILL),
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
            ),
            tooltip="Turn hands-free kiosk voice navigation on or off",
        )
    controller["button"] = voice_button
    right.extend([voice_status, voice_button])
    if voice_enabled and not controller["active"]:
        page.run_task(start_voice)

    if session_label:
        right.append(
            ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=5),
                border_radius=Radius.PILL,
                bgcolor=Colors.PRIMARY_MUTED,
                border=ft.border.all(1, ft.Colors.with_opacity(0.15, Colors.PRIMARY)),
                content=ft.Row(
                    spacing=6, tight=True,
                    controls=[
                        ft.Icon(ft.Icons.PERSON_ROUNDED, size=14, color=Colors.PRIMARY),
                        ft.Text(session_label, size=12, color=Colors.PRIMARY,
                                weight=ft.FontWeight.W_600, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                ),
            )
        )
        if not compact:
            right.append(
                ft.TextButton(
                    "End session",
                    icon=ft.Icons.LOGOUT_ROUNDED,
                    style=ft.ButtonStyle(
                        color=Colors.ERROR,
                        enable_feedback=False,
                    ),
                    on_click=lambda _e: (state.clear_kiosk(), page.go(Routes.HOME)),
                )
            )
        else:
            right.append(
                ft.IconButton(
                    icon=ft.Icons.LOGOUT_ROUNDED,
                    tooltip="End private session",
                    icon_color=Colors.ERROR,
                    on_click=lambda _e: (state.clear_kiosk(), page.go(Routes.HOME)),
                )
            )

    if show_home:
        right.append(
            ft.IconButton(
                icon=ft.Icons.HOME_OUTLINED,
                tooltip="Home",
                icon_color=Colors.TEXT_SECONDARY,
                icon_size=20,
                style=ft.ButtonStyle(enable_feedback=False,
                                     shape=ft.RoundedRectangleBorder(radius=Radius.SM)),
                on_click=lambda _e: page.go(Routes.HOME),
            )
        )

    right.append(ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=5),
        border_radius=Radius.PILL,
        bgcolor=Colors.SUCCESS_BG if health_ok else Colors.ERROR_BG,
        content=ft.Row(spacing=5, controls=[
            ft.Icon(ft.Icons.CLOUD_DONE_OUTLINED if health_ok else ft.Icons.CLOUD_OFF_OUTLINED, size=14, color=health_color),
            *([] if compact else [ft.Text(health_label, size=10, color=health_color, weight=ft.FontWeight.W_600)]),
        ]),
        tooltip=f"{health_label}. API, database, and Gemini configuration status.",
    ))

    return ft.Container(
        height=64,
        bgcolor=Colors.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)),
        shadow=ft.BoxShadow(
            blur_radius=14,
            color=ft.Colors.with_opacity(0.05, Colors.PRIMARY_DARK),
            offset=ft.Offset(0, 3),
        ),
        padding=ft.padding.symmetric(
            horizontal=Spacing.LG if not compact else Spacing.MD,
            vertical=0,
        ),
        content=ft.Row(
            expand=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(expand=True, spacing=Spacing.SM, controls=left),
                ft.Row(spacing=Spacing.XS, controls=right),
            ],
        ),
    )
