"""
LIBRAI – Book Card
==================
Refined card for search results, recommendations, popular books, etc.
Vertical book-spine orientation: cover → category label → title →
author → availability tag → shelf.
"""

from __future__ import annotations
from typing import Callable, Optional
import flet as ft

from core.theme import Colors, Radius, Spacing, Shadow


def _availability(copies: int, total: int) -> ft.Container:
    if copies > 0:
        bg, fg, text = Colors.SUCCESS_BG,  Colors.SUCCESS,         f"{copies} available"
    elif total <= 0:
        bg, fg, text = Colors.SURFACE_ALT, Colors.TEXT_DISABLED,   "No copies"
    else:
        bg, fg, text = Colors.WARNING_BG,  Colors.WARNING,         "All borrowed"
    return ft.Container(
        bgcolor=bg, border_radius=Radius.PILL,
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        content=ft.Text(text, size=10, weight=ft.FontWeight.W_700, color=fg),
    )


def BookCard(book: dict, on_click: Optional[Callable] = None) -> ft.Container:
    avail  = int(book.get("available_copies", 0))
    total  = int(book.get("total_copies", 0))
    shelf  = str(book.get("shelf_location") or "")
    cat    = str(book.get("category") or "GENERAL").upper()

    cover: ft.Control = (
        ft.Image(src=book["cover_url"], width=138, height=184,
                 fit=ft.ImageFit.COVER, border_radius=Radius.MD)
        if book.get("cover_url")
        else ft.Container(
            width=138, height=184,
            border_radius=Radius.MD,
            bgcolor=Colors.PRIMARY_MUTED,
            alignment=ft.alignment.center,
            content=ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, size=44, color=Colors.PRIMARY_LIGHT),
        )
    )

    return ft.Container(
        width=210,
        border_radius=Radius.LG,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        shadow=Shadow.xs(),
        padding=Spacing.MD,
        ink=False,
        on_click=on_click,
        content=ft.Column(
            spacing=Spacing.SM,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            controls=[
                # Cover image — centred
                ft.Container(alignment=ft.alignment.center, content=cover),
                ft.Container(height=2),
                # Category eyebrow
                ft.Text(cat, size=9, weight=ft.FontWeight.W_700,
                        color=Colors.PRIMARY),
                # Title
                ft.Text(
                    book.get("title", "Untitled"),
                    size=13, weight=ft.FontWeight.W_700,
                    max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                    color=Colors.TEXT_PRIMARY,
                ),
                # Author
                ft.Text(
                    book.get("author", "Unknown"),
                    size=11, color=Colors.TEXT_SECONDARY,
                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Container(expand=True),
                # Footer row
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        _availability(avail, total),
                        ft.Text(shelf, size=10, color=Colors.TEXT_DISABLED),
                    ],
                ),
            ],
        ),
    )
