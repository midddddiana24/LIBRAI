"""
LIBRAI – Alert Banner
=====================
Inline status banner. Maps RequestState values to semantic colours
from the design system. Consistent across kiosk and admin pages.
"""

from __future__ import annotations
from typing import Optional
import flet as ft

from core.constants import RequestState
from core.theme import Colors, Radius, Spacing

_STYLES: dict[str, tuple[str, str, str, str]] = {
    # kind:  (bg, fg, icon, default_title)
    RequestState.VALIDATION_ERROR: (Colors.WARNING_BG,  Colors.WARNING, ft.Icons.WARNING_AMBER_ROUNDED,    "Check your input"),
    RequestState.AUTH_ERROR:       (Colors.ERROR_BG,    Colors.ERROR,   ft.Icons.LOCK_OUTLINE_ROUNDED,     "Session expired"),
    RequestState.PERMISSION_ERROR: (Colors.ERROR_BG,    Colors.ERROR,   ft.Icons.BLOCK_ROUNDED,            "Not permitted"),
    RequestState.SERVER_ERROR:     (Colors.ERROR_BG,    Colors.ERROR,   ft.Icons.ERROR_OUTLINE_ROUNDED,    "Server error"),
    RequestState.NETWORK_ERROR:    (Colors.ERROR_BG,    Colors.ERROR,   ft.Icons.WIFI_OFF_ROUNDED,         "Connection problem"),
    "success":                     (Colors.SUCCESS_BG,  Colors.SUCCESS, ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, "Success"),
    "info":                        (Colors.INFO_BG,     Colors.INFO,    ft.Icons.INFO_OUTLINE_ROUNDED,     "Information"),
}
_FALLBACK = (Colors.ERROR_BG, Colors.ERROR, ft.Icons.ERROR_OUTLINE_ROUNDED, "Something went wrong")


def Alert(
    kind: str,
    message: str,
    title: Optional[str] = None,
    on_dismiss=None,
) -> ft.Container:
    bg, fg, icon, default_title = _STYLES.get(kind, _FALLBACK)

    close_btn: ft.Control = ft.Container()
    if on_dismiss:
        close_btn = ft.IconButton(
            icon=ft.Icons.CLOSE_ROUNDED,
            icon_color=fg, icon_size=16,
            style=ft.ButtonStyle(enable_feedback=False),
            on_click=on_dismiss,
        )

    return ft.Container(
        bgcolor=bg,
        border_radius=Radius.MD,
        border=ft.border.only(left=ft.BorderSide(3, fg)),
        padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=Spacing.SM + 4),
        content=ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.START,
            controls=[
                ft.Icon(icon, size=18, color=fg),
                ft.Container(width=Spacing.SM),
                ft.Column(
                    expand=True, spacing=2,
                    controls=[
                        ft.Text(title or default_title,
                                size=13, weight=ft.FontWeight.W_700, color=fg),
                        ft.Text(message, size=12, color=fg),
                    ],
                ),
                close_btn,
            ],
        ),
    )
