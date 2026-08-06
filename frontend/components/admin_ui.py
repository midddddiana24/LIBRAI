"""
LIBRAI – Admin UI Primitives
============================
Shared building blocks used exclusively inside the administrative workspace.
Kept separate from kiosk components so their styles can diverge cleanly.
"""

from __future__ import annotations
from typing import Callable
import flet as ft

from core.theme import Colors, Radius, Spacing, Shadow


# ─────────────────────────────────────────────────────────────
#  STATUS BADGE
# ─────────────────────────────────────────────────────────────
_STATUS: dict[str, tuple[str, str]] = {
    "active":    (Colors.SUCCESS_BG,  Colors.SUCCESS),
    "available": (Colors.SUCCESS_BG,  Colors.SUCCESS),
    "returned":  (Colors.SUCCESS_BG,  Colors.SUCCESS),
    "borrowed":  (Colors.WARNING_BG,  Colors.WARNING),
    "reserved":  (Colors.INFO_BG,     Colors.INFO),
    "ready":     (Colors.INFO_BG,     Colors.INFO),
    "overdue":   (Colors.ERROR_BG,    Colors.ERROR),
    "lost":      (Colors.ERROR_BG,    Colors.ERROR),
    "damaged":   (Colors.ERROR_BG,    Colors.ERROR),
    "inactive":  (Colors.SURFACE_ALT, Colors.TEXT_SECONDARY),
    "suspended": (Colors.WARNING_BG,  Colors.WARNING),
    "archived":  (Colors.SURFACE_ALT, Colors.TEXT_SECONDARY),
}


def status_badge(value: object) -> ft.Container:
    text = str(value or "unknown").strip().lower()
    bg, fg = _STATUS.get(text, (Colors.SURFACE_ALT, Colors.TEXT_SECONDARY))
    return ft.Container(
        bgcolor=bg,
        border_radius=Radius.PILL,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        content=ft.Text(
            text.replace("_", " ").title(),
            size=11, weight=ft.FontWeight.W_700, color=fg,
        ),
    )


# ─────────────────────────────────────────────────────────────
#  SECTION CARD
# ─────────────────────────────────────────────────────────────
def section_card(
    content: ft.Control,
    padding: int | ft.Padding = Spacing.LG,
    title: str | None = None,
    subtitle: str | None = None,
    height: int | None = None,
) -> ft.Container:
    """White bordered card.  Optional header row if title is supplied."""
    inner: ft.Control
    if title:
        heading = ft.Column(
            tight=True, spacing=2,
            controls=[
                ft.Text(title, size=15, weight=ft.FontWeight.W_700,
                        color=Colors.TEXT_PRIMARY),
                *([] if not subtitle else
                  [ft.Text(subtitle, size=12, color=Colors.TEXT_SECONDARY)]),
            ],
        )
        inner = ft.Column(
            tight=True, spacing=Spacing.MD,
            controls=[
                heading,
                ft.Container(height=0.8, bgcolor=Colors.BORDER),
                content,
            ],
        )
    else:
        inner = content

    return ft.Container(
        bgcolor=Colors.SURFACE,
        height=height,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.XL,
        padding=padding,
        shadow=Shadow.sm(),
        content=inner,
    )


# ─────────────────────────────────────────────────────────────
#  TABLE SHELL
# ─────────────────────────────────────────────────────────────
def table_shell(table: ft.DataTable) -> ft.Container:
    # A DataTable otherwise keeps only its intrinsic column width, leaving a
    # large blank area on widescreen admin pages. Expand it within the
    # scrollable row so Books, Users, and report tables consume the workspace.
    table.expand = True
    return ft.Container(
        expand=True,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.XL,
        shadow=Shadow.sm(),
        padding=0,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Row(expand=True, scroll=ft.ScrollMode.AUTO, controls=[table]),
    )


# ─────────────────────────────────────────────────────────────
#  TEXT FIELDS
# ─────────────────────────────────────────────────────────────
def admin_text_field(**kwargs) -> ft.TextField:
    """Consistent admin text input — quiet fill, clear focus ring."""
    multiline = bool(kwargs.get("multiline"))
    kwargs.setdefault("text_size",          13)
    kwargs.setdefault("filled",             True)
    kwargs.setdefault("fill_color",         Colors.SURFACE_ALT)
    kwargs.setdefault("bgcolor",            Colors.SURFACE_ALT)
    kwargs.setdefault("border",             ft.InputBorder.OUTLINE)
    kwargs.setdefault("border_radius",      Radius.MD)
    kwargs.setdefault("border_width",       1)
    kwargs.setdefault("border_color",       Colors.BORDER_STRONG)
    kwargs.setdefault("focused_border_width", 1.5)
    kwargs.setdefault("focused_border_color", Colors.PRIMARY)
    kwargs.setdefault("focused_bgcolor",    Colors.SURFACE)
    kwargs.setdefault("content_padding",
                      ft.padding.symmetric(horizontal=14, vertical=13))
    kwargs.setdefault("label_style",
                      ft.TextStyle(size=12, color=Colors.TEXT_SECONDARY))
    kwargs.setdefault("hint_style",
                      ft.TextStyle(size=13, color=Colors.TEXT_DISABLED))
    if not multiline:
        kwargs.setdefault("height", 50)
    return ft.TextField(**kwargs)


def admin_search_field(**kwargs) -> ft.TextField:
    kwargs.setdefault("prefix_icon",    ft.Icons.SEARCH_ROUNDED)
    kwargs.setdefault("height",         44)
    kwargs.setdefault("content_padding",
                      ft.padding.symmetric(horizontal=14, vertical=10))
    kwargs.setdefault("hint_text",      "Search…")
    return admin_text_field(**kwargs)


def admin_dropdown(**kwargs) -> ft.Dropdown:
    kwargs.setdefault("text_size",          13)
    kwargs.setdefault("filled",             True)
    kwargs.setdefault("fill_color",         Colors.SURFACE_ALT)
    kwargs.setdefault("bgcolor",            Colors.SURFACE_ALT)
    kwargs.setdefault("border",             ft.InputBorder.OUTLINE)
    kwargs.setdefault("border_radius",      Radius.MD)
    kwargs.setdefault("border_width",       1)
    kwargs.setdefault("border_color",       Colors.BORDER_STRONG)
    kwargs.setdefault("focused_border_width", 1.5)
    kwargs.setdefault("focused_border_color", Colors.PRIMARY)
    kwargs.setdefault("content_padding",
                      ft.padding.symmetric(horizontal=14, vertical=12))
    kwargs.setdefault("label_style",
                      ft.TextStyle(size=12, color=Colors.TEXT_SECONDARY))
    return ft.Dropdown(**kwargs)


# ─────────────────────────────────────────────────────────────
#  FORM SECTION
# ─────────────────────────────────────────────────────────────
def form_section(
    title: str,
    subtitle: str,
    controls: list[ft.Control],
) -> ft.Column:
    return ft.Column(
        tight=True, spacing=10,
        controls=[
            ft.Text(title, size=13, weight=ft.FontWeight.W_700,
                    color=Colors.TEXT_PRIMARY),
            ft.Text(subtitle, size=11, color=Colors.TEXT_SECONDARY),
            ft.ResponsiveRow(spacing=12, run_spacing=12, controls=controls),
        ],
    )


def page_intro(description: str) -> ft.Text:
    return ft.Text(description, color=Colors.TEXT_SECONDARY, size=13)


# ─────────────────────────────────────────────────────────────
#  DIALOGS
# ─────────────────────────────────────────────────────────────
def confirmation_dialog(
    page: ft.Page,
    title: str,
    message: str,
    confirm_label: str,
    on_confirm: Callable,
    danger: bool = False,
) -> None:
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Text(message, size=14),
        actions=[
            ft.TextButton("Cancel",
                          on_click=lambda _e: page.close(dialog)),
            ft.FilledButton(
                confirm_label,
                style=ft.ButtonStyle(
                    bgcolor=Colors.ERROR if danger else Colors.PRIMARY,
                    color=Colors.ON_PRIMARY,
                ),
                on_click=lambda e: on_confirm(e, dialog),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dialog)


def qr_dialog(
    page: ft.Page,
    title: str,
    image_source: str,
    identifier: str,
    replaced: bool = False,
    download_url: str | None = None,
) -> None:
    notice_text = (
        "The previous QR is now invalid.  Print and issue this replacement securely."
        if replaced
        else "Print or photograph this QR and issue it to the user securely."
    )
    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(title),
        content=ft.Container(
            width=320,
            content=ft.Column(
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Spacing.SM,
                controls=[
                    ft.Image(src=image_source, width=256, height=256,
                             fit=ft.ImageFit.CONTAIN),
                    ft.Text(identifier, selectable=True, size=11,
                            color=Colors.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        bgcolor=Colors.WARNING_BG,
                        border_radius=Radius.SM,
                        padding=Spacing.SM,
                        content=ft.Text(notice_text, size=11, color=Colors.WARNING,
                                        text_align=ft.TextAlign.CENTER),
                    ),
                ],
            ),
        ),
        actions=[
            *(
                [ft.FilledButton(
                    "Download PNG",
                    icon=ft.Icons.DOWNLOAD_ROUNDED,
                    on_click=lambda _e: page.launch_url(download_url),
                )]
                if download_url else []
            ),
            ft.OutlinedButton("Done", on_click=lambda _e: page.close(dialog)),
        ],
    )
    page.open(dialog)
