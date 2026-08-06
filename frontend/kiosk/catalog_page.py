"""Shared backend-ranked discovery catalog."""

from __future__ import annotations

import flet as ft

from components.alert import Alert
from components.book_grid import BookGrid
from components.page_shell import KioskView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors
from services.ai_service import ai_service


def build_catalog(page: ft.Page, route: str, title: str, subtitle: str, kind: str) -> ft.View:
    state = get_state(page)
    user_id = state.kiosk_user.get("id") if state.kiosk_user else None
    grant = state.kiosk_user.get("verification_token") if state.kiosk_user else None
    result = ai_service.recommend(user_id=user_id, kind=kind, user_verification_token=grant)
    controls: list[ft.Control] = [ft.Text(title, size=28, weight=ft.FontWeight.W_700), ft.Text(subtitle, color=Colors.TEXT_SECONDARY)]
    if result.ok:
        books = result.data.get("items", result.data.get("books", [])) if isinstance(result.data, dict) else result.data
        controls.append(BookGrid(books, on_book_click=lambda book: lambda _e: page.go(f"{Routes.BOOK_DETAILS}/{book['id']}")))
    else:
        controls.append(Alert(result.error_kind, result.message))
    return KioskView(page, route, title, controls, state.kiosk_user.get("name") if state.kiosk_user else None)
