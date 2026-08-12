from __future__ import annotations
import flet as ft
from components.admin_ui import section_card, status_badge
from components.alert import Alert
from components.sidebar import AdminView
from core.constants import Routes
from core.theme import Colors, Spacing
from services.api_client import api_client

def build(page: ft.Page) -> ft.View:
    rows = ft.Column(spacing=Spacing.SM)
    page_index = 0
    page_size = 25
    previous = ft.IconButton(ft.Icons.CHEVRON_LEFT_ROUNDED, tooltip="Previous page")
    next_button = ft.IconButton(ft.Icons.CHEVRON_RIGHT_ROUNDED, tooltip="Next page")
    def load(_event=None):
        result = api_client.get("/notifications/admin/email-deliveries", params={"offset": page_index * page_size, "limit": page_size})
        rows.controls.clear()
        if not result.ok:
            rows.controls.append(Alert(result.error_kind, result.message))
        else:
            items = result.data.get("items", []) if isinstance(result.data, dict) else []
            for item in items:
                detail = item.get("error") or f"Created {item.get('created_at', '—')}"
                rows.controls.append(section_card(ft.Row(controls=[ft.Column(expand=True, tight=True, controls=[ft.Text(str(item.get("subject", "Notification")), weight=ft.FontWeight.W_600), ft.Text(str(item.get("recipient", "—")), size=12, color=Colors.TEXT_SECONDARY), ft.Text(detail, size=11, color=Colors.ERROR if item.get("error") else Colors.TEXT_DISABLED)]), status_badge(item.get("status", "pending"))], vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=Spacing.MD))
            if not items: rows.controls.append(ft.Text("No email deliveries are queued.", color=Colors.TEXT_SECONDARY))
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
    content = ft.Column(spacing=Spacing.LG, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Column(tight=True, controls=[ft.Text("Email Deliveries", size=26, weight=ft.FontWeight.W_700), ft.Text("Monitor queued notification delivery. Sending requires a configured worker.", color=Colors.TEXT_SECONDARY)]), ft.IconButton(ft.Icons.REFRESH_ROUNDED, tooltip="Refresh", on_click=load)]), rows, ft.Row(alignment=ft.MainAxisAlignment.END, controls=[previous, next_button])])
    load()
    return AdminView(page, Routes.ADMIN_EMAIL_DELIVERIES, "Email Deliveries", content, subtitle="Notification queue monitoring")
