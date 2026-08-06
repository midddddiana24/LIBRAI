"""Detailed kiosk catalog view with accurate copy and reservation states."""

from __future__ import annotations

import flet as ft

from components.alert import Alert
from components.book_grid import BookGrid
from components.page_shell import KioskView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing, touch_button_style
from services.book_service import book_service
from services.reservation_service import reservation_service


def _chip(label: str) -> ft.Container:
    return ft.Container(bgcolor=Colors.INFO_BG, border_radius=Radius.PILL, padding=ft.padding.symmetric(horizontal=10, vertical=5), content=ft.Text(label, size=11, color=Colors.INFO, weight=ft.FontWeight.W_600))


def build(page: ft.Page) -> ft.View:
    state = get_state(page)
    try:
        book_id = int(page.route.rstrip("/").split("/")[-1])
    except ValueError:
        book_id = 0
    result = book_service.get_book(book_id)
    if not result.ok:
        return KioskView(page, page.route, "Book Details", [Alert(result.error_kind, result.message)])
    book = result.data
    notice = ft.Column()
    available = int(book.get("available_copies", 0))
    total = int(book.get("total_copies", 0))

    def reserve(_event) -> None:
        if total <= 0:
            notice.controls = [Alert("info", "This title has no physical copies and cannot be reserved.")]
        elif not state.kiosk_user:
            notice.controls = [Alert("info", "Open My Account and scan your library QR before reserving.")]
        else:
            response = reservation_service.create(state.kiosk_user["id"], book["id"], state.kiosk_user.get("verification_token"))
            notice.controls = [Alert("success", f"Reservation created. Queue position: {response.data.get('position', 'pending')}")] if response.ok else [Alert(response.error_kind, response.message)]
        page.update()

    if available > 0:
        availability = ft.Container(bgcolor=Colors.SUCCESS_BG, border_radius=Radius.MD, padding=Spacing.MD, content=ft.Row(controls=[ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=Colors.SUCCESS), ft.Column(tight=True, controls=[ft.Text(f"{available} of {total} copies available", weight=ft.FontWeight.W_600, color=Colors.SUCCESS), ft.Text(f"Shelf location: {book.get('shelf_location') or 'Ask a librarian'}", size=12, color=Colors.SUCCESS)])]))
        action = ft.FilledButton("Start borrowing", icon=ft.Icons.QR_CODE_SCANNER_ROUNDED, style=touch_button_style(), on_click=lambda _e: page.go(Routes.BORROW_SCAN_USER))
    elif total > 0:
        availability = ft.Container(bgcolor=Colors.WARNING_BG, border_radius=Radius.MD, padding=Spacing.MD, content=ft.Row(controls=[ft.Icon(ft.Icons.SCHEDULE_ROUNDED, color=Colors.WARNING), ft.Column(tight=True, controls=[ft.Text("All physical copies are currently borrowed", weight=ft.FontWeight.W_600, color=Colors.WARNING), ft.Text("You may join the reservation queue.", size=12, color=Colors.WARNING)])]))
        action = ft.FilledButton("Reserve book", icon=ft.Icons.BOOKMARK_ADD_ROUNDED, style=touch_button_style(bg_color=Colors.WARNING), on_click=reserve)
    else:
        availability = ft.Container(bgcolor="#F1F5F9", border_radius=Radius.MD, padding=Spacing.MD, content=ft.Row(controls=[ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, color=Colors.TEXT_SECONDARY), ft.Column(tight=True, controls=[ft.Text("No physical copies in the library", weight=ft.FontWeight.W_600), ft.Text("Ask library staff about this catalog record.", size=12, color=Colors.TEXT_SECONDARY)])]))
        action = ft.OutlinedButton("Not in circulation", icon=ft.Icons.BLOCK_ROUNDED, disabled=True)

    cover = ft.Container(width=230, height=320, bgcolor="#E8EDF7", border_radius=Radius.MD, clip_behavior=ft.ClipBehavior.ANTI_ALIAS, alignment=ft.alignment.center, content=ft.Image(src=book.get("cover_url"), width=230, height=320, fit=ft.ImageFit.COVER) if book.get("cover_url") else ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, size=76, color=Colors.PRIMARY))
    keywords = [str(value) for value in [*(book.get("subjects") or []), *(book.get("keywords") or [])] if value]
    details = ft.Column(
        expand=True,
        spacing=Spacing.MD,
        controls=[
            ft.Column(tight=True, spacing=4, controls=[ft.Text(str(book.get("title") or "Untitled"), size=30, weight=ft.FontWeight.W_700), ft.Text(f"by {book.get('author') or 'Unknown author'}", size=16, color=Colors.TEXT_SECONDARY)]),
            ft.Row(wrap=True, controls=[_chip(str(book.get("category") or "Uncategorized")), *[_chip(value) for value in keywords[:5]]]),
            ft.Text(str(book.get("description") or "No description is available for this title."), size=14, color=Colors.TEXT_PRIMARY),
            availability,
            ft.ResponsiveRow(spacing=12, run_spacing=8, controls=[ft.Text(f"ISBN\n{book.get('isbn') or '—'}", col={"sm":6,"md":3}, size=12), ft.Text(f"Publisher\n{book.get('publisher') or '—'}", col={"sm":6,"md":3}, size=12), ft.Text(f"Publication year\n{book.get('publication_year') or '—'}", col={"sm":6,"md":3}, size=12), ft.Text(f"Shelf\n{book.get('shelf_location') or '—'}", col={"sm":6,"md":3}, size=12)]),
            action,
            notice,
        ],
    )
    similar = book.get("similar_books") or []
    return KioskView(page, page.route, "Book Details", [ft.ResponsiveRow(spacing=Spacing.XL, run_spacing=Spacing.LG, controls=[ft.Container(col={"sm":12,"md":3}, alignment=ft.alignment.top_center, content=cover), ft.Container(col={"sm":12,"md":9}, content=details)]), ft.Divider(color=Colors.BORDER), ft.Text("Similar books", size=21, weight=ft.FontWeight.W_600), BookGrid(similar, on_book_click=lambda item: lambda _e: page.go(f"{Routes.BOOK_DETAILS}/{item['id']}"), empty_message="No similar books yet", empty_subtitle="More titles in this category will appear here.")])
