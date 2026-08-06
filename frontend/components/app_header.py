"""
LIBRAI – Kiosk App Header
=========================
Thin, refined top bar shown on every kiosk sub-page.
Reads from the design system — no hardcoded colors here.
"""

from __future__ import annotations
import flet as ft

from components.brand_logo import BrandLogo
from core.config   import settings
from core.constants import APP_NAME, Routes
from core.state    import get_state
from core.theme    import Colors, Radius, Spacing


def AppHeader(
    page: ft.Page,
    title: str | None = None,
    show_back: bool = False,
    session_label: str | None = None,
    show_home: bool = True,
) -> ft.Container:
    state   = get_state(page)
    compact = (getattr(page, "width", None) or 1366) < 820

    # ── Left cluster ──────────────────────────────────────────
    left: list[ft.Control] = []

    if show_back:
        left.append(
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                icon_color=Colors.TEXT_PRIMARY,
                icon_size=20,
                tooltip="Go back",
                style=ft.ButtonStyle(enable_feedback=False,
                                     shape=ft.RoundedRectangleBorder(radius=Radius.SM)),
                on_click=lambda _e: page.go(Routes.HOME),
            )
        )

    # Logo mark
    left.append(
        ft.Row(
            spacing=Spacing.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                BrandLogo(52, 42),
                ft.Column(
                    spacing=0,
                    tight=True,
                    controls=[
                        ft.Text(APP_NAME, size=15, weight=ft.FontWeight.W_800,
                                color=Colors.TEXT_PRIMARY),
                        ft.Text(
                            settings.library_name,
                            size=10,
                            color=Colors.TEXT_SECONDARY,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                ),
            ],
        )
    )

    # Page title divider + label
    if title and not compact:
        left += [
            ft.Container(width=1, height=24, bgcolor=Colors.BORDER,
                         margin=ft.margin.symmetric(horizontal=4)),
            ft.Text(title, size=13, weight=ft.FontWeight.W_600,
                    color=Colors.TEXT_SECONDARY, max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS),
        ]

    # ── Right cluster ─────────────────────────────────────────
    right: list[ft.Control] = []

    if session_label:
        right.append(
            ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=5),
                border_radius=Radius.PILL,
                bgcolor=Colors.PRIMARY_MUTED,
                border=ft.border.all(1, ft.Colors.with_opacity(0.15, Colors.PRIMARY)),
                content=ft.Row(
                    spacing=6, tight=True,
                    controls=[
                        ft.Icon(ft.Icons.PERSON_ROUNDED, size=14, color=Colors.PRIMARY),
                        ft.Text(session_label, size=12, color=Colors.PRIMARY,
                                weight=ft.FontWeight.W_600, max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                ),
            )
        )
        if not compact:
            right.append(
                ft.TextButton(
                    "End session",
                    icon=ft.Icons.LOGOUT_ROUNDED,
                    style=ft.ButtonStyle(
                        color=Colors.ERROR,
                        enable_feedback=False,
                    ),
                    on_click=lambda _e: (state.clear_kiosk(), page.go(Routes.HOME)),
                )
            )
        else:
            right.append(
                ft.IconButton(
                    icon=ft.Icons.LOGOUT_ROUNDED,
                    tooltip="End private session",
                    icon_color=Colors.ERROR,
                    on_click=lambda _e: (state.clear_kiosk(), page.go(Routes.HOME)),
                )
            )

    if show_home:
        right.append(
            ft.IconButton(
                icon=ft.Icons.HOME_OUTLINED,
                tooltip="Home",
                icon_color=Colors.TEXT_SECONDARY,
                icon_size=20,
                style=ft.ButtonStyle(enable_feedback=False,
                                     shape=ft.RoundedRectangleBorder(radius=Radius.SM)),
                on_click=lambda _e: page.go(Routes.HOME),
            )
        )

    return ft.Container(
        height=64,
        bgcolor=Colors.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)),
        shadow=ft.BoxShadow(
            blur_radius=14,
            color=ft.Colors.with_opacity(0.05, Colors.PRIMARY_DARK),
            offset=ft.Offset(0, 3),
        ),
        padding=ft.padding.symmetric(
            horizontal=Spacing.LG if not compact else Spacing.MD,
            vertical=0,
        ),
        content=ft.Row(
            expand=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(expand=True, spacing=Spacing.SM, controls=left),
                ft.Row(spacing=Spacing.XS, controls=right),
            ],
        ),
    )
