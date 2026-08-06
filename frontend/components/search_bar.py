"""
LIBRAI – Search Bar
===================
Touch-first search input used on the kiosk home page, search page,
and AI assistant page. Renders cleanly on both dark and light surfaces.
"""

from __future__ import annotations
from typing import Callable, Optional
import flet as ft

from core.theme import Colors, Radius, Spacing


def SearchBar(
    on_submit: Callable[[str], None],
    on_mic_click: Optional[Callable] = None,
    hint_text: str = "Search by title, author, ISBN, or keyword…",
    autofocus: bool = False,
    on_surface_dark: bool = False,     # True when placed on the navy hero banner
    compact: bool = False,
) -> ft.Container:
    """Pill-shaped search bar.

    Args:
        on_submit: called with the raw text when Enter / search icon pressed.
        on_mic_click: shows a microphone button when provided.
        hint_text: placeholder.
        autofocus: pass True on dedicated search pages.
        on_surface_dark: adjusts surface/border colours for dark-bg placement.
    """
    surface_bg     = "rgba(255,255,255,0.96)" if on_surface_dark else Colors.SURFACE
    border_color   = ft.Colors.with_opacity(0.20, "#FFFFFF") if on_surface_dark else Colors.BORDER

    field = ft.TextField(
        hint_text=hint_text,
        hint_style=ft.TextStyle(size=13 if compact else 14, color=Colors.TEXT_DISABLED),
        text_style=ft.TextStyle(size=13 if compact else 14, color=Colors.TEXT_PRIMARY),
        border=ft.InputBorder.NONE,
        expand=True,
        content_padding=ft.padding.symmetric(vertical=10 if compact else 15),
        autofocus=autofocus,
        on_submit=lambda e: on_submit(e.control.value or ""),
    )

    trailing: list[ft.Control] = []

    if on_mic_click:
        trailing.append(
            ft.Container(
                width=34 if compact else 40, height=34 if compact else 40,
                border_radius=Radius.PILL,
                bgcolor=ft.Colors.with_opacity(0.08, Colors.PRIMARY),
                alignment=ft.alignment.center,
                tooltip="Voice search",
                content=ft.Icon(ft.Icons.MIC_ROUNDED, size=16 if compact else 18, color=Colors.PRIMARY),
                on_click=on_mic_click,
            )
        )

    trailing.append(
        ft.Container(
            width=36 if compact else 42, height=36 if compact else 42,
            border_radius=Radius.PILL,
            bgcolor=Colors.PRIMARY,
            alignment=ft.alignment.center,
            tooltip="Search",
            shadow=ft.BoxShadow(blur_radius=8,
                                color=ft.Colors.with_opacity(0.25, Colors.PRIMARY),
                                offset=ft.Offset(0, 3)),
            content=ft.Icon(ft.Icons.SEARCH_ROUNDED, size=16 if compact else 18, color=Colors.ON_PRIMARY),
            on_click=lambda _e: on_submit(field.value or ""),
        )
    )

    return ft.Container(
        bgcolor=surface_bg,
        border=ft.border.all(1, border_color),
        border_radius=Radius.PILL,
        shadow=ft.BoxShadow(blur_radius=22,
                            color=ft.Colors.with_opacity(0.10, Colors.PRIMARY_DARK),
                            offset=ft.Offset(0, 7)),
        padding=ft.padding.only(
            left=Spacing.MD if compact else Spacing.LG,
            right=5 if compact else 6,
            top=3 if compact else 4,
            bottom=3 if compact else 4,
        ),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.SEARCH_OUTLINED, size=16 if compact else 18, color=Colors.TEXT_DISABLED),
                ft.Container(width=6),
                field,
                *trailing,
                ft.Container(width=2),
            ],
        ),
    )
