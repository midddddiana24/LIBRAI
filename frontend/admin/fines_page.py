from __future__ import annotations
import flet as ft
from components.admin_ui import section_card, status_badge
from components.alert import Alert
from components.sidebar import AdminView
from core.constants import Routes
from core.theme import Colors, Spacing
from services.api_client import api_client

def build(page: ft.Page) -> ft.View:
    notice = ft.Column()
    rows = ft.Column(spacing=Spacing.SM)
    page_index = 0
    page_size = 25
    previous = ft.IconButton(ft.Icons.CHEVRON_LEFT_ROUNDED, tooltip="Previous page")
    next_button = ft.IconButton(ft.Icons.CHEVRON_RIGHT_ROUNDED, tooltip="Next page")

    def load(_event=None):
        result = api_client.get("/fines", params={"status": "UNPAID", "offset": page_index * page_size, "limit": page_size})
        rows.controls.clear()
        if not result.ok:
            rows.controls.append(Alert(result.error_kind, result.message))
        else:
            items = result.data.get("items", []) if isinstance(result.data, dict) else []
            if not items:
                rows.controls.append(ft.Text("No unpaid fines require attention.", color=Colors.TEXT_SECONDARY))
            for item in items:
                pay = ft.FilledButton("Mark paid", icon=ft.Icons.PAYMENTS_OUTLINED)
                def settle(_event, current=item, button=pay):
                    button.disabled = True
                    page.update()
                    response = api_client.post(f"/fines/{current['id']}/pay", {"note": "Settled by admin"})
                    if response.ok:
                        load()
                    else:
                        button.disabled = False
                        notice.controls = [Alert(response.error_kind, response.message)]
                        page.update()
                pay.on_click = settle
                rows.controls.append(section_card(ft.Row(controls=[ft.Column(expand=True, tight=True, controls=[ft.Text(str(item.get("book_title", "Borrowing fine")), weight=ft.FontWeight.W_600), ft.Text(f"User {item.get('user_id', '—')} · {item.get('reason', 'Overdue')}", size=12, color=Colors.TEXT_SECONDARY)]), ft.Text(f"PHP {int(item.get('amount_cents', 0))/100:.2f}", weight=ft.FontWeight.W_700, color=Colors.ERROR), status_badge(item.get("status", "unpaid")), pay], vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=Spacing.MD))
        page.update()

    def previous_page(_event):
        nonlocal page_index
        if page_index:
            page_index -= 1
            load()

    def next_page(_event):
        nonlocal page_index
        page_index += 1
        load()

    previous.on_click = previous_page
    next_button.on_click = next_page

    content = ft.Column(spacing=Spacing.LG, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Column(tight=True, controls=[ft.Text("Unpaid Fines", size=26, weight=ft.FontWeight.W_700), ft.Text("Review and settle overdue borrowing charges.", color=Colors.TEXT_SECONDARY)]), ft.IconButton(ft.Icons.REFRESH_ROUNDED, tooltip="Refresh", on_click=load)]), notice, rows, ft.Row(alignment=ft.MainAxisAlignment.END, controls=[previous, next_button])])
    load()
    return AdminView(page, Routes.ADMIN_FINES, "Fines", content, subtitle="Payment review and settlement")
