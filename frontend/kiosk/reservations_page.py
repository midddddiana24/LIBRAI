"""Private reservation queue with secure user cancellation."""

from __future__ import annotations

import flet as ft

from components.alert import Alert
from components.empty_state import EmptyState
from components.page_shell import KioskView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing
from services.reservation_service import reservation_service
from utils.formatting import format_date


def build(page: ft.Page) -> ft.View:
    state = get_state(page)
    if not state.kiosk_user:
        return KioskView(page, Routes.RESERVATIONS, "My Reservations", [EmptyState("Library QR required", "Open My Account and scan your QR before viewing private reservations.", ft.Icons.LOCK_ROUNDED, "Go to My Account", lambda _e: page.go(Routes.ACCOUNT))])
    content = ft.Column(spacing=Spacing.MD)
    notice = ft.Column()

    def cancel(item: dict) -> None:
        def confirm(_event) -> None:
            response = reservation_service.cancel(int(item["id"]), state.kiosk_user.get("verification_token"))
            page.close(dialog)
            notice.controls = [Alert("success", "Reservation cancelled.")] if response.ok else [Alert(response.error_kind, response.message)]
            load()

        dialog = ft.AlertDialog(modal=True, title=ft.Text("Cancel reservation?"), content=ft.Text(f"Remove your reservation for {item.get('book_title', 'this book')}?"), actions=[ft.TextButton("Keep reservation", on_click=lambda _e: page.close(dialog)), ft.FilledButton("Cancel reservation", on_click=confirm)])
        page.open(dialog)

    def load() -> None:
        response = reservation_service.list(state.kiosk_user["id"], state.kiosk_user.get("verification_token"))
        content.controls.clear()
        if not response.ok:
            content.controls.append(Alert(response.error_kind, response.message))
        else:
            payload = response.data if isinstance(response.data, dict) else {"items": response.data}
            rows = [item for item in payload.get("items", []) if str(item.get("status", "")).lower() in {"active", "ready"}]
            if not rows:
                content.controls.append(EmptyState("No active reservations", "Reserved books and queue positions will appear here.", ft.Icons.BOOKMARK_BORDER_ROUNDED))
            for item in rows:
                ready = str(item.get("status", "")).lower() == "ready"
                content.controls.append(ft.Container(bgcolor=Colors.SURFACE, border=ft.border.all(1, Colors.BORDER), border_radius=Radius.MD, padding=Spacing.MD, content=ft.Row(controls=[ft.Container(width=58, height=76, border_radius=Radius.SM, bgcolor="#E8EDF7", alignment=ft.alignment.center, content=ft.Image(src=item.get("cover_url"), fit=ft.ImageFit.COVER) if item.get("cover_url") else ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=Colors.PRIMARY)), ft.Column(expand=True, tight=True, spacing=3, controls=[ft.Text(str(item.get("book_title", "Reserved book")), weight=ft.FontWeight.W_600), ft.Text(str(item.get("book_author") or ""), size=12, color=Colors.TEXT_SECONDARY), ft.Text("Ready for pickup" if ready else f"Queue position: {item.get('position', '—')}", color=Colors.SUCCESS if ready else Colors.PRIMARY, weight=ft.FontWeight.W_600), ft.Text(f"Reserved {format_date(item.get('reserved_at'))}", size=11, color=Colors.TEXT_SECONDARY)]), ft.OutlinedButton("Cancel", icon=ft.Icons.CLOSE_ROUNDED, on_click=lambda _e, row=item: cancel(row))])))
        page.update()

    load()
    return KioskView(page, Routes.RESERVATIONS, "My Reservations", [ft.Text("My Reservations", size=27, weight=ft.FontWeight.W_700), ft.Text("Track your queue position or cancel reservations you no longer need.", color=Colors.TEXT_SECONDARY), notice, content], state.kiosk_user.get("name"))
