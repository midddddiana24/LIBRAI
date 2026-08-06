"""
LIBRAI – Loading & Progress Views
===================================
Consistent loading spinners and multi-step transaction progress.
Used during borrow/return validation pipelines.
"""

from __future__ import annotations
import flet as ft

from components.brand_logo import BrandLogo
from core.theme import Colors, Radius, Spacing


def BrandedLoadingView(route: str, message: str = "Preparing your workspace") -> ft.View:
    """Full-page route transition with unmistakable branded feedback."""
    return ft.View(
        route=route,
        padding=0,
        bgcolor=Colors.BACKGROUND,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Container(
                    width=330,
                    padding=ft.padding.symmetric(horizontal=36, vertical=32),
                    bgcolor=Colors.SURFACE,
                    border=ft.border.all(1, Colors.BORDER),
                    border_radius=Radius.XL,
                    shadow=ft.BoxShadow(
                        blur_radius=30,
                        color=ft.Colors.with_opacity(0.09, Colors.PRIMARY_DARK),
                        offset=ft.Offset(0, 10),
                    ),
                    content=ft.Column(
                        tight=True,
                        spacing=Spacing.MD,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            BrandLogo(104, 82),
                            ft.Text(
                                message,
                                size=16,
                                weight=ft.FontWeight.W_700,
                                color=Colors.TEXT_PRIMARY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Text(
                                "Loading the latest library information…",
                                size=12,
                                color=Colors.TEXT_SECONDARY,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.ProgressBar(
                                height=4,
                                color=Colors.BRAND_GREEN,
                                bgcolor=Colors.PRIMARY_MUTED,
                                border_radius=Radius.PILL,
                            ),
                        ],
                    ),
                ),
            )
        ],
    )


def LoadingView(message: str = "Loading…") -> ft.Container:
    return ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.MD,
            controls=[
                ft.ProgressRing(
                    color=Colors.PRIMARY,
                    width=44, height=44, stroke_width=3.5,
                ),
                ft.Text(message, size=13, color=Colors.TEXT_SECONDARY),
            ],
        ),
    )


def InlineLoading(message: str = "Loading…") -> ft.Container:
    """Compact loading surface for tables, filters, and dialog actions."""
    return ft.Container(
        height=92,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.LG,
        alignment=ft.alignment.center,
        content=ft.Row(
            tight=True,
            spacing=Spacing.MD,
            controls=[
                ft.ProgressRing(width=22, height=22, stroke_width=2.5, color=Colors.PRIMARY),
                ft.Column(tight=True, spacing=2, controls=[ft.Text(message, size=13, weight=ft.FontWeight.W_600), ft.Text("Please wait while LIBRAI completes this action.", size=11, color=Colors.TEXT_SECONDARY)]),
            ],
        ),
    )


def set_button_loading(button: ft.Control, loading: bool, idle_text: str, loading_text: str = "Processing…") -> None:
    """Apply consistent duplicate-click protection and button messaging."""
    button.disabled = loading
    if hasattr(button, "text"):
        button.text = loading_text if loading else idle_text


def StepProgressView(
    steps: list[str],
    current_step_index: int,
    title: str = "Processing your request…",
) -> ft.Container:
    """Animated step checklist for multi-validation flows.

    Args:
        steps: ordered list of step descriptions.
        current_step_index: index currently in progress.
            Items before it = done. Items after = pending.
    """
    rows: list[ft.Control] = []
    for i, step in enumerate(steps):
        if i < current_step_index:
            icon_ctrl: ft.Control = ft.Icon(
                ft.Icons.CHECK_CIRCLE_ROUNDED, size=18, color=Colors.SUCCESS)
            text_color = Colors.TEXT_SECONDARY
        elif i == current_step_index:
            icon_ctrl = ft.ProgressRing(
                color=Colors.PRIMARY, width=18, height=18, stroke_width=2.5)
            text_color = Colors.TEXT_PRIMARY
        else:
            icon_ctrl = ft.Icon(
                ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED, size=18,
                color=Colors.TEXT_DISABLED)
            text_color = Colors.TEXT_DISABLED

        rows.append(
            ft.Row(
                spacing=Spacing.SM,
                controls=[
                    ft.Container(width=22, alignment=ft.alignment.center,
                                 content=icon_ctrl),
                    ft.Text(step, size=14, color=text_color),
                ],
            )
        )

    return ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.LG,
            controls=[
                ft.ProgressRing(color=Colors.PRIMARY,
                                width=52, height=52, stroke_width=4),
                ft.Text(title, size=18, weight=ft.FontWeight.W_700,
                        color=Colors.TEXT_PRIMARY),
                ft.Container(
                    width=360,
                    content=ft.Column(spacing=10, controls=rows),
                ),
            ],
        ),
    )
