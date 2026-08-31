"""Grounded library assistant with visible request and fallback states."""

from __future__ import annotations

import flet as ft
import flet_audio_recorder as far
import uuid
import asyncio
import time
import wave
from pathlib import Path

from components.alert import Alert
from components.book_grid import BookGrid
from components.page_shell import KioskView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing
from services.ai_service import ai_service
from services.speech_service import speech_service
from services.voice_command_service import resolve_voice_command
from core.config import settings


def cleanup_stale_recordings(max_age_seconds: int = 3600) -> None:
    """Remove abandoned voice recordings from interrupted sessions."""
    root = settings.frontend_upload_directory.resolve()
    if not root.exists():
        return
    cutoff = time.time() - max_age_seconds
    for candidate in root.glob("speech-*"):
        try:
            if candidate.is_file() and candidate.stat().st_mtime < cutoff:
                candidate.unlink()
        except OSError:
            continue


def build(page: ft.Page) -> ft.View:
    state = get_state(page)
    cleanup_stale_recordings()
    transcript = ft.Column(spacing=Spacing.MD)
    prompt = ft.TextField(expand=True, hint_text="Ask what kind of book you are looking for…", multiline=True, min_lines=1, max_lines=3, border_radius=Radius.MD)
    speech = ft.Text("Use the microphone to speak your search.", size=11, color=Colors.TEXT_SECONDARY)
    progress = ft.Row(visible=False, controls=[ft.ProgressRing(width=20, height=20, stroke_width=3), ft.Text("Searching the library catalog…", size=12, color=Colors.TEXT_SECONDARY)])
    ask_button = ft.FilledButton("Ask", icon=ft.Icons.SEND_ROUNDED)
    recording = {"active": False, "last_spoken": "", "pending_command": None}

    # One microphone service per page, shared with the header controller.
    # Rebuilding this route must not stack extra AudioRecorder services.
    header_controller = getattr(page, "_librai_voice_controller", None)
    recorder = None
    if not getattr(page, "web", False):
        buffer = {"data": bytearray()}

        def on_audio_stream(event) -> None:
            chunk = getattr(event, "chunk", b"")
            if chunk:
                buffer["data"] += bytes(chunk)

        recorder = far.AudioRecorder(
            on_stream=on_audio_stream,
            configuration=far.AudioRecorderConfiguration(
                encoder=far.AudioEncoder.PCM16BITS,
                channels=1,
                sample_rate=16000,
                suppress_noise=True,
                cancel_echo=True,
                auto_gain=True,
            ),
        )
        if header_controller is None:
            page.overlay.append(recorder)
        # Strong reference so Flet's service garbage collector does not
        # unregister this recorder between events; rebuilt pages replace it.
        setattr(page, "_librai_assistant_recorder", recorder)
        recording["buffer"] = buffer

    mic_button = ft.IconButton(ft.Icons.MIC_NONE_ROUNDED, tooltip="Speak your search")
    command_mode = "dictate"
    mode = ft.Dropdown(width=155, label="Voice mode", value=command_mode, options=[ft.dropdown.Option("dictate", "Dictate text"), ft.dropdown.Option("command", "Voice command")], border_radius=Radius.SM)

    async def complete_recording() -> None:
        if not recording["active"]:
            return
        recording["active"] = False
        mic_button.icon = ft.Icons.MIC_NONE_ROUNDED
        mic_button.tooltip = "Speak your search"
        speech.value = "Processing speech..."
        speech.color = Colors.PRIMARY
        page.update()
        await recorder.stop_recording()
        buffer = recording.get("buffer")
        captured = bytes(buffer["data"]) if buffer else b""
        if buffer:
            buffer["data"] = bytearray()
        if not captured:
            speech.value = "No recording was captured. You can type your request instead."
            speech.color = Colors.ERROR
            page.update()
            return
        path = settings.frontend_upload_directory / f"speech-{uuid.uuid4().hex}.wav"
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(captured)
        result = await asyncio.to_thread(speech_service.transcribe, str(path))
        cleanup_recording(str(path))
        if result.ok:
            await process_spoken(str((result.data or {}).get("text", "")).strip())
        else:
            speech.value = f"Speech failed: {result.message} You can type your request instead."
            speech.color = Colors.ERROR
        page.update()

    async def auto_stop() -> None:
        await asyncio.sleep(6 if mode.value == "command" else 15)
        if recording["active"]:
            await complete_recording()

    async def toggle_recording(_event=None) -> None:
        if recorder is None:
            speech.value = "Browser microphone is unavailable in this Flet web build. Type your request instead."
            speech.color = Colors.WARNING
            page.update()
            return
        if recording["active"]:
            await complete_recording()
            return
        settings.frontend_upload_directory.mkdir(parents=True, exist_ok=True)
        buffer = recording.get("buffer")
        if buffer:
            buffer["data"] = bytearray()
        try:
            if await recorder.start_recording():
                recording["active"] = True
                mic_button.icon = ft.Icons.STOP_CIRCLE_OUTLINED
                mic_button.tooltip = "Stop recording"
                speech.value = "Listening (up to 15 seconds)"
                speech.color = Colors.PRIMARY
                page.run_task(auto_stop)
            else:
                speech.value = "This device could not start microphone recording. You can type instead."
                speech.color = Colors.ERROR
        except Exception as exc:
            speech.value = f"Microphone error: {type(exc).__name__}. Check Windows microphone permission, then try again—or type instead."
            speech.color = Colors.ERROR
        page.update()

    def cleanup_recording(path: str | None) -> None:
        if not path or str(path).startswith(("blob:", "http://", "https://")):
            return
        candidate = Path(path).resolve()
        root = settings.frontend_upload_directory.resolve()
        if candidate.is_file() and root in candidate.parents:
            candidate.unlink()

    async def process_spoken(spoken: str) -> None:
        recording["last_spoken"] = spoken
        command = resolve_voice_command(spoken)
        # A recognized kiosk intent must work from every voice entry point.
        # Older sessions can reopen this page in "dictate" mode, but that
        # must not turn "I want to borrow a book" into an assistant question.
        if command["action"] not in {"unknown", "ask"}:
            speech.value = command["message"]
            speech.color = Colors.SUCCESS
            if command["action"] == "navigate":
                page.go(command["route"])
            elif command["action"] in {"search", "search_available", "clear_search"}:
                page.client_storage.set("librai_pending_search", command["query"])
                page.client_storage.set("librai_pending_available_only", command["action"] == "search_available")
                page.go(Routes.SEARCH)
            elif command["action"] == "back":
                page.go(Routes.HOME)
            return
        if mode.value != "command":
            prompt.value = spoken
            speech.value = "Speech converted to text. Review it, then press Ask."
            speech.color = Colors.SUCCESS
            return
        if command["action"] in {"unknown", "ask"}:
            prompt.value = command.get("query", spoken)
            speech.value = "Command not recognized. I placed the speech in the text box."
            speech.color = Colors.WARNING
            return

    async def repeat_command(_event) -> None:
        if recording["last_spoken"]:
            await process_spoken(recording["last_spoken"])
            page.update()

    mic_button.on_click = toggle_recording

    def add_exchange(query: str, data: dict) -> None:
        transcript.controls.append(ft.Container(alignment=ft.alignment.center_right, content=ft.Container(bgcolor=Colors.INFO_BG, border_radius=Radius.MD, padding=Spacing.MD, content=ft.Text(query))))
        fallback = bool(data.get("fallback_used"))
        conversational = data.get("response_type") == "conversation"
        interaction_id = data.get("interaction_id")
        feedback = ft.Row(spacing=4, visible=bool(interaction_id), controls=[ft.Text("Was this useful?",size=11,color=Colors.TEXT_SECONDARY)])

        def rate(_event, helpful: bool) -> None:
            state.touch()
            result = ai_service.feedback(int(interaction_id), helpful, state.kiosk_user.get("id") if state.kiosk_user else None, state.kiosk_user.get("verification_token") if state.kiosk_user else None)
            feedback.controls = [ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,color=Colors.SUCCESS,size=16),ft.Text("Feedback recorded. Thank you.",size=11,color=Colors.SUCCESS)] if result.ok else [ft.Text(result.message,size=11,color=Colors.ERROR)]
            page.update()

        if interaction_id:
            feedback.controls.extend([ft.IconButton(ft.Icons.THUMB_UP_OUTLINED,tooltip="Helpful",icon_size=17,on_click=lambda event:rate(event,True)),ft.IconButton(ft.Icons.THUMB_DOWN_OUTLINED,tooltip="Not helpful",icon_size=17,on_click=lambda event:rate(event,False))])
        intent=data.get("parsed_intent") or {}
        intent_text=" • ".join([*(intent.get("topics") or [])[:3], *([str(intent["level"]).title()] if intent.get("level") else [])])
        transcript.controls.append(ft.Container(bgcolor=Colors.SURFACE, border=ft.border.all(1, Colors.BORDER), border_radius=Radius.MD, padding=Spacing.LG, content=ft.Column(controls=[ft.Row(controls=[ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color="#7C3AED"), ft.Text("LIBRAI Assistant", weight=ft.FontWeight.W_600), ft.Container(expand=True), ft.Text("Conversation" if conversational else "Catalog fallback" if fallback else "AI assisted", size=11, color=Colors.PRIMARY if conversational else Colors.WARNING if fallback else Colors.SUCCESS)]), *([ft.Text(f"Understood: {intent_text}",size=11,color=Colors.PRIMARY)] if intent_text and not conversational else []), ft.Text(str(data.get("answer") or data.get("message") or "Here are matching books.")), *([] if conversational else [BookGrid(data.get("books", []), on_book_click=lambda book: lambda _e: page.go(f"{Routes.BOOK_DETAILS}/{book['id']}"))]),feedback])))

    for message in state.ai_messages:
        add_exchange(str(message.get("query", "")), message.get("response", {}))

    async def ask(_event=None) -> None:
        state.touch()
        query = str(prompt.value or "").strip()
        if not query or ask_button.disabled:
            return
        ask_button.disabled = True
        progress.visible = True
        page.update()
        result = await asyncio.to_thread(
            ai_service.search,
            query,
            state.kiosk_user.get("id") if state.kiosk_user else None,
            state.kiosk_user.get("verification_token") if state.kiosk_user else None,
        )
        progress.visible = False
        ask_button.disabled = False
        if result.ok:
            state.ai_messages.append({"query": query, "response": result.data})
            add_exchange(query, result.data)
            prompt.value = ""
        else:
            transcript.controls.append(Alert(result.error_kind, result.message))
        page.update()

    def clear(_event) -> None:
        state.touch()
        state.ai_messages.clear()
        transcript.controls.clear()
        page.update()

    ask_button.on_click = ask
    examples = ft.Row(wrap=True, controls=[ft.OutlinedButton(text, on_click=lambda _e, value=text: (setattr(prompt, "value", value), page.update())) for text in ["Beginner cybersecurity books", "Python programming books", "Networking fundamentals"]])
    command_help = ft.Container(
        bgcolor=Colors.INFO_BG,
        border_radius=Radius.SM,
        padding=Spacing.MD,
        content=ft.Column(tight=True, spacing=4, controls=[
            ft.Text("Voice command examples", size=12, weight=ft.FontWeight.W_700, color=Colors.PRIMARY),
            ft.Text("Borrow a book  •  Return a book  •  Search Python books  •  Show my account  •  Go home", size=11, color=Colors.TEXT_SECONDARY),
        ]),
    )
    if command_mode == "command":
        mic_button.visible = False
        mode.visible = False
    composer = ft.Container(bgcolor=Colors.SURFACE, border=ft.border.all(1, Colors.BORDER), border_radius=Radius.MD, padding=Spacing.MD, content=ft.Column(controls=[ft.Row(controls=[prompt, mode, mic_button, ask_button]), progress, speech, command_help]))
    return KioskView(page, Routes.AI_ASSISTANT, "LIBRAI Assistant", [ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Column(tight=True, controls=[ft.Text("What would you like to read?", size=28, weight=ft.FontWeight.W_700), ft.Text("Recommendations are limited to books in the library catalog.", color=Colors.TEXT_SECONDARY)]), ft.TextButton("Clear conversation", icon=ft.Icons.DELETE_OUTLINE_ROUNDED, on_click=clear)]), examples, transcript, composer], state.kiosk_user.get("name") if state.kiosk_user else None)
