"""
LIBRAI – Empty State
====================
Friendly zero-result illustration shown in grids, tables,
reservations, borrowing history, etc.
"""

from __future__ import annotations
from typing import Callable, Optional
import flet as ft

from core.theme import Colors, Radius, Spacing


def EmptyState(
    title: str,
    subtitle: str = "",
    icon: str = "inbox_rounded",
    action_label: Optional[str] = None,
    on_action: Optional[Callable] = None,
) -> ft.Container:
    controls: list[ft.Control] = [
        ft.Container(
            width=72, height=72,
            border_radius=Radius.XL,
            bgcolor=Colors.SURFACE_ALT,
            alignment=ft.alignment.center,
            content=ft.Icon(icon, size=34, color=Colors.TEXT_DISABLED),
        ),
        ft.Container(height=4),
        ft.Text(title, size=16, weight=ft.FontWeight.W_700,
                color=Colors.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
    ]
    if subtitle:
        controls.append(
            ft.Text(subtitle, size=13, color=Colors.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER)
        )
    if action_label and on_action:
        controls.append(ft.Container(height=4))
        controls.append(ft.FilledButton(action_label, on_click=on_action))

    return ft.Container(
        padding=Spacing.XXL,
        alignment=ft.alignment.center,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.SM,
            controls=controls,
        ),
    )
