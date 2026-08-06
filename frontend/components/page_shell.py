from __future__ import annotations

import flet as ft

from components.app_header import AppHeader
from core.theme import Colors, Spacing


def KioskView(page: ft.Page, route: str, title: str, controls: list[ft.Control], session_label: str | None = None) -> ft.View:
    get_state = __import__("core.state", fromlist=["get_state"]).get_state
    state = get_state(page)
    state.touch()
    page.on_keyboard_event = lambda _event: state.touch()
    compact = (getattr(page, "width", None) or 1366) < 820
    return ft.View(
        route=route,
        padding=0,
        bgcolor=Colors.BACKGROUND,
        controls=[
            AppHeader(page, title=title, show_back=True, session_label=session_label),
            ft.Container(
                expand=True,
                alignment=ft.alignment.top_center,
                content=ft.Container(
                    width=980,
                    padding=ft.padding.symmetric(horizontal=Spacing.MD if compact else Spacing.XL, vertical=Spacing.LG if compact else Spacing.XL),
                    on_hover=lambda _event: state.touch(),
                    content=ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=Spacing.MD if compact else Spacing.LG, controls=controls),
                ),
            ),
        ],
    )
