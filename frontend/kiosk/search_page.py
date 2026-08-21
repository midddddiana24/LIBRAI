"""Searchable, filterable, and paginated kiosk catalog."""

from __future__ import annotations

import flet as ft

from components.alert import Alert
from components.book_grid import BookGrid
from components.loading_view import InlineLoading
from components.page_shell import KioskView
from components.search_bar import SearchBar
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing
from services.book_service import book_service


PAGE_SIZE = 24


def build(page: ft.Page) -> ft.View:
    app_state = get_state(page)
    search_state = {"query": "", "offset": 0, "total": 0}
    stored_recent = page.client_storage.get("librai_recent_searches") or []
    recent_searches = [str(value) for value in stored_recent][:5] if isinstance(stored_recent, list) else []
    results = ft.Column(spacing=Spacing.MD)
    notice = ft.Column()
    pager = ft.Row(alignment=ft.MainAxisAlignment.END, spacing=Spacing.SM)

    category_result = book_service.list_categories()
    categories = [str(item.get("name")) for item in category_result.data] if category_result.ok and isinstance(category_result.data, list) else []
    category = ft.Dropdown(label="Category", width=210, options=[ft.dropdown.Option("All"), *[ft.dropdown.Option(x) for x in categories]], value="All", border_radius=Radius.SM)
    author = ft.TextField(label="Author", width=200, border_radius=Radius.SM)
    year = ft.TextField(label="Publication year", width=175, keyboard_type=ft.KeyboardType.NUMBER, border_radius=Radius.SM)
    sort = ft.Dropdown(label="Sort by", width=180, value="title", options=[ft.dropdown.Option("title", "Title A–Z"), ft.dropdown.Option("newest", "Newest added"), ft.dropdown.Option("availability", "Availability")], border_radius=Radius.SM)
    available = ft.Checkbox(label="Available only")
    recent_row = ft.Row(wrap=True, spacing=Spacing.SM, run_spacing=Spacing.SM)

    def render_recent() -> None:
        recent_row.controls = [
            ft.Text("Recent", size=11, color=Colors.TEXT_SECONDARY),
            *[ft.OutlinedButton(value, icon=ft.Icons.HISTORY_ROUNDED, on_click=lambda _event, query=value: execute(query)) for value in recent_searches],
        ] if recent_searches else []

    def execute(query: str | None = None, reset: bool = True, show_loading: bool = True) -> None:
        app_state.touch()
        if query is not None:
            search_state["query"] = query.strip()
            if search_state["query"]:
                normalized = search_state["query"]
                recent_searches[:] = [normalized, *[item for item in recent_searches if item.lower() != normalized.lower()]][:5]
                page.client_storage.set("librai_recent_searches", recent_searches)
                render_recent()
        if reset:
            search_state["offset"] = 0
        raw_year = str(year.value or "").strip()
        if raw_year and (not raw_year.isdigit() or not 1000 <= int(raw_year) <= 2200):
            notice.controls = [Alert("validation_error", "Enter a valid publication year between 1000 and 2200.")]
            page.update()
            return
        notice.controls.clear()
        if show_loading:
            results.controls = [InlineLoading("Searching the library catalog…")]
            page.update()
        response = book_service.list_books(
            query=search_state["query"] or None,
            category=None if category.value == "All" else category.value,
            author=str(author.value or "").strip() or None,
            available_only=bool(available.value),
            publication_year=int(raw_year) if raw_year else None,
            sort=str(sort.value or "title"),
            offset=search_state["offset"],
            limit=PAGE_SIZE,
        )
        results.controls.clear()
        if not response.ok:
            results.controls.append(Alert(response.error_kind, response.message))
        else:
            payload = response.data if isinstance(response.data, dict) else {"items": response.data, "total": len(response.data)}
            books = payload.get("items", [])
            search_state["total"] = int(payload.get("total", len(books)))
            results.controls.extend([
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(f"{search_state['total']} books found", weight=ft.FontWeight.W_600), ft.Text("Demo data" if response.is_mock else "Live catalog", size=12, color=Colors.WARNING if response.is_mock else Colors.SUCCESS)]),
                BookGrid(books, on_book_click=lambda book: lambda _e: page.go(f"{Routes.BOOK_DETAILS}/{book['id']}")),
            ])
        start = search_state["offset"] + 1 if search_state["total"] else 0
        end = min(search_state["offset"] + PAGE_SIZE, search_state["total"])
        pager.controls = [
            ft.Text(f"{start}–{end} of {search_state['total']}", color=Colors.TEXT_SECONDARY),
            ft.IconButton(ft.Icons.CHEVRON_LEFT_ROUNDED, tooltip="Previous page", disabled=search_state["offset"] == 0, on_click=previous),
            ft.IconButton(ft.Icons.CHEVRON_RIGHT_ROUNDED, tooltip="Next page", disabled=search_state["offset"] + PAGE_SIZE >= search_state["total"], on_click=next_page),
        ]
        page.update()

    def previous(_event) -> None:
        search_state["offset"] = max(0, search_state["offset"] - PAGE_SIZE)
        execute(reset=False)

    def next_page(_event) -> None:
        search_state["offset"] += PAGE_SIZE
        execute(reset=False)

    def clear(_event) -> None:
        category.value = "All"
        author.value = ""
        year.value = ""
        sort.value = "title"
        available.value = False
        search_state["query"] = ""
        execute()

    pending = page.client_storage.get("librai_pending_search") or ""
    pending_available = bool(page.client_storage.get("librai_pending_available_only"))
    page.client_storage.remove("librai_pending_search")
    page.client_storage.remove("librai_pending_available_only")
    available.value = pending_available
    render_recent()
    execute(str(pending), show_loading=False)
    filters = ft.Container(
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.MD,
        padding=Spacing.MD,
        content=ft.Row(wrap=True, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[category, author, year, sort, available, ft.FilledButton("Apply", icon=ft.Icons.FILTER_ALT_ROUNDED, on_click=lambda _e: execute()), ft.TextButton("Clear", on_click=clear)]),
    )
    return KioskView(page, Routes.SEARCH, "Search Books", [ft.Text("Find your next book", size=26, weight=ft.FontWeight.BOLD), ft.Text("Search the school catalog by title, author, ISBN, subject, or keyword.", color=Colors.TEXT_SECONDARY), SearchBar(on_submit=lambda query: execute(query), hint_text="Search title, author, ISBN, subject, or keyword…", autofocus=True), recent_row, filters, notice, results, pager])
