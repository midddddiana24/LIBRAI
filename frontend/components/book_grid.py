"""
LIBRAI - Book grid component.

Wraps a list of book dicts into a responsive wrap-layout of BookCard
components, with a built-in empty state when there are no results.
"""

from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from components.book_card import BookCard
from components.empty_state import EmptyState
from core.theme import Spacing


def BookGrid(
    books: list[dict],
    on_book_click: Optional[Callable[[dict], Callable]] = None,
    empty_message: str = "No books found",
    empty_subtitle: str = "Try a different search term or filter.",
) -> ft.Control:
    """Build a responsive grid of book cards.

    Args:
        books: list of book dicts (backend schema).
        on_book_click: function(book) -> callback(e). Called per-card so
            each card's on_click closes over the correct book.
        empty_message / empty_subtitle: shown when `books` is empty.
    """

    if not books:
        return EmptyState(icon="search_off_rounded", title=empty_message, subtitle=empty_subtitle)

    def _handler(book: dict):
        if on_book_click is None:
            return None
        return on_book_click(book)

    return ft.Row(
        wrap=True,
        spacing=Spacing.MD,
        run_spacing=Spacing.MD,
        controls=[BookCard(book, on_click=_handler(book)) for book in books],
    )
