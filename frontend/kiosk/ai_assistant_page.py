"""Grounded library assistant with visible request and fallback states."""

from __future__ import annotations

import flet as ft
import uuid
import asyncio

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


def build(page: ft.Page) -> ft.View:
    state = get_state(page)
    transcript = ft.Column(spacing=Spacing.MD)
    prompt = ft.TextField(expand=True, hint_text="Ask what kind of book you are looking for…", multiline=True, min_lines=1, max_lines=3, border_radius=Radius.MD)
    speech = ft.Text("Use the microphone to speak your search.", size=11, color=Colors.TEXT_SECONDARY)
    progress = ft.Row(visible=False, controls=[ft.ProgressRing(width=20, height=20, stroke_width=3), ft.Text("Searching the library catalog…", size=12, color=Colors.TEXT_SECONDARY)])
    ask_button = ft.FilledButton("Ask", icon=ft.Icons.SEND_ROUNDED)
    recorder = ft.AudioRecorder(suppress_noise=True, cancel_echo=True, auto_gain=True, sample_rate=16000)
    page.overlay.append(recorder)
    recording = {"active": False}
    mic_button = ft.IconButton(ft.Icons.MIC_NONE_ROUNDED, tooltip="Speak your search")
    command_mode = page.client_storage.get("librai_voice_mode") or "dictate"
    page.client_storage.remove("librai_voice_mode")
    mode = ft.Dropdown(width=155, label="Voice mode", value=command_mode, options=[ft.dropdown.Option("dictate", "Dictate text"), ft.dropdown.Option("command", "Voice command")], border_radius=Radius.SM)

    async def toggle_recording(_event) -> None:
        if recording["active"]:
            path = await asyncio.to_thread(recorder.stop_recording)
            recording["active"] = False
            mic_button.icon = ft.Icons.MIC_NONE_ROUNDED
            mic_button.tooltip = "Speak your search"
            if not path:
                speech.value = "No recording was captured. Please try again."
                speech.color = Colors.ERROR
            else:
                result = speech_service.transcribe(str(path))
                if result.ok:
                    spoken = str((result.data or {}).get("text", "")).strip()
                    if mode.value == "command":
                        command = resolve_voice_command(spoken)
                        speech.value = command["message"]
                        speech.color = Colors.SUCCESS if command["action"] != "unknown" else Colors.ERROR
                        if command["action"] == "navigate":
                            page.go(command["route"])
                        elif command["action"] == "search":
                            page.client_storage.set("librai_pending_search", command["query"])
                            page.go(Routes.SEARCH)
                        elif command["action"] == "ask":
                            prompt.value = command["query"]
                            ask()
                    else:
                        prompt.value = spoken
                        speech.value = "Speech converted to text. Review it, then press Ask."
                        speech.color = Colors.SUCCESS
                else:
                    speech.value = result.message
                    speech.color = Colors.ERROR
            page.update()
            return
        settings.frontend_upload_directory.mkdir(parents=True, exist_ok=True)
        output = settings.frontend_upload_directory / f"speech-{uuid.uuid4().hex}.wav"
        try:
            if await asyncio.to_thread(recorder.start_recording, str(output)):
                recording["active"] = True
                mic_button.icon = ft.Icons.STOP_CIRCLE_OUTLINED
                mic_button.tooltip = "Stop recording"
                speech.value = "Listening… press the microphone again when finished."
                speech.color = Colors.PRIMARY
            else:
                speech.value = "This device could not start microphone recording."
                speech.color = Colors.ERROR
        except Exception:
            speech.value = "Microphone permission or recording is unavailable on this device."
            speech.color = Colors.ERROR
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
    composer = ft.Container(bgcolor=Colors.SURFACE, border=ft.border.all(1, Colors.BORDER), border_radius=Radius.MD, padding=Spacing.MD, content=ft.Column(controls=[ft.Row(controls=[prompt, mode, mic_button, ask_button]), progress, speech, command_help]))
    return KioskView(page, Routes.AI_ASSISTANT, "LIBRAI Assistant", [ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Column(tight=True, controls=[ft.Text("What would you like to read?", size=28, weight=ft.FontWeight.W_700), ft.Text("Recommendations are limited to books in the library catalog.", color=Colors.TEXT_SECONDARY)]), ft.TextButton("Clear conversation", icon=ft.Icons.DELETE_OUTLINE_ROUNDED, on_click=clear)]), examples, transcript, composer], state.kiosk_user.get("name") if state.kiosk_user else None)
