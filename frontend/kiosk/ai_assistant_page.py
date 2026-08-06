"""Grounded library assistant with visible request and fallback states."""

from __future__ import annotations

import flet as ft

from components.alert import Alert
from components.book_grid import BookGrid
from components.page_shell import KioskView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing
from services.ai_service import ai_service


def build(page: ft.Page) -> ft.View:
    state = get_state(page)
    transcript = ft.Column(spacing=Spacing.MD)
    prompt = ft.TextField(expand=True, hint_text="Ask what kind of book you are looking for…", multiline=True, min_lines=1, max_lines=3, border_radius=Radius.MD)
    speech = ft.Text("Voice input is unavailable on this kiosk. Typed search remains fully available.", size=11, color=Colors.TEXT_SECONDARY)
    progress = ft.Row(visible=False, controls=[ft.ProgressRing(width=20, height=20, stroke_width=3), ft.Text("Searching the library catalog…", size=12, color=Colors.TEXT_SECONDARY)])
    ask_button = ft.FilledButton("Ask", icon=ft.Icons.SEND_ROUNDED)

    def add_exchange(query: str, data: dict) -> None:
        transcript.controls.append(ft.Container(alignment=ft.alignment.center_right, content=ft.Container(bgcolor=Colors.INFO_BG, border_radius=Radius.MD, padding=Spacing.MD, content=ft.Text(query))))
        fallback = bool(data.get("fallback_used"))
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
        transcript.controls.append(ft.Container(bgcolor=Colors.SURFACE, border=ft.border.all(1, Colors.BORDER), border_radius=Radius.MD, padding=Spacing.LG, content=ft.Column(controls=[ft.Row(controls=[ft.Icon(ft.Icons.AUTO_AWESOME_ROUNDED, color="#7C3AED"), ft.Text("LIBRAI Assistant", weight=ft.FontWeight.W_600), ft.Container(expand=True), ft.Text("Catalog fallback" if fallback else "AI assisted", size=11, color=Colors.WARNING if fallback else Colors.SUCCESS)]), *([ft.Text(f"Understood: {intent_text}",size=11,color=Colors.PRIMARY)] if intent_text else []), ft.Text(str(data.get("answer") or data.get("message") or "Here are matching books.")), BookGrid(data.get("books", []), on_book_click=lambda book: lambda _e: page.go(f"{Routes.BOOK_DETAILS}/{book['id']}")),feedback])))

    for message in state.ai_messages:
        add_exchange(str(message.get("query", "")), message.get("response", {}))

    def ask(_event) -> None:
        state.touch()
        query = str(prompt.value or "").strip()
        if not query or ask_button.disabled:
            return
        ask_button.disabled = True
        progress.visible = True
        page.update()
        result = ai_service.search(query, state.kiosk_user.get("id") if state.kiosk_user else None, state.kiosk_user.get("verification_token") if state.kiosk_user else None)
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
    composer = ft.Container(bgcolor=Colors.SURFACE, border=ft.border.all(1, Colors.BORDER), border_radius=Radius.MD, padding=Spacing.MD, content=ft.Column(controls=[ft.Row(controls=[prompt, ft.IconButton(ft.Icons.MIC_OFF_ROUNDED, tooltip="Voice input is not configured", disabled=True), ask_button]), progress, speech]))
    return KioskView(page, Routes.AI_ASSISTANT, "LIBRAI Assistant", [ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Column(tight=True, controls=[ft.Text("What would you like to read?", size=28, weight=ft.FontWeight.W_700), ft.Text("Recommendations are limited to books in the library catalog.", color=Colors.TEXT_SECONDARY)]), ft.TextButton("Clear conversation", icon=ft.Icons.DELETE_OUTLINE_ROUNDED, on_click=clear)]), examples, transcript, composer], state.kiosk_user.get("name") if state.kiosk_user else None)
