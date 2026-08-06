"""
LIBRAI – Stat Card
==================
KPI tile used on any summary page (dashboard, reports overview).
Refined version: value top-left, icon top-right, note below value.
"""

from __future__ import annotations
from typing import Optional
import flet as ft

from core.theme import Colors, Radius, Spacing, Shadow


def StatCard(
    label: str,
    value: str,
    icon: str = ft.Icons.INSIGHTS_ROUNDED,
    accent_color: str = Colors.PRIMARY,
    note: str = "",
    trend_text: Optional[str] = None,
    trend_positive: bool = True,
) -> ft.Container:
    trend: ft.Control = ft.Container()
    if trend_text:
        c = Colors.SUCCESS if trend_positive else Colors.ERROR
        i = ft.Icons.ARROW_UPWARD_ROUNDED if trend_positive else ft.Icons.ARROW_DOWNWARD_ROUNDED
        trend = ft.Row(
            tight=True, spacing=3,
            controls=[
                ft.Icon(i, size=12, color=c),
                ft.Text(trend_text, size=11, color=c, weight=ft.FontWeight.W_600),
            ],
        )

    return ft.Container(
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.LG,
        shadow=Shadow.xs(),
        padding=Spacing.LG,
        content=ft.Column(
            tight=True, spacing=Spacing.MD,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            tight=True, spacing=3,
                            controls=[
                                ft.Text(value, size=28,
                                        weight=ft.FontWeight.W_800,
                                        color=Colors.TEXT_PRIMARY),
                                ft.Text(label, size=13,
                                        color=Colors.TEXT_SECONDARY),
                            ],
                        ),
                        ft.Container(
                            width=46, height=46,
                            border_radius=Radius.MD,
                            bgcolor=ft.Colors.with_opacity(0.10, accent_color),
                            alignment=ft.alignment.center,
                            content=ft.Icon(icon, size=22, color=accent_color),
                        ),
                    ],
                ),
                *([ft.Text(note, size=11, color=Colors.TEXT_DISABLED)] if note else []),
                *([trend] if trend_text else []),
            ],
        ),
    )
