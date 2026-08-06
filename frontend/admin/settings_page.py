"""Professional library policy and workstation settings page."""

from __future__ import annotations

import flet as ft

from components.admin_ui import admin_text_field, page_intro, section_card
from components.alert import Alert
from components.loading_view import set_button_loading
from components.sidebar import AdminView
from core.config import settings
from core.constants import Routes
from core.theme import Colors, Radius, Spacing
from services.admin_service import admin_service


def build(page: ft.Page) -> ft.View:
    result = admin_service.settings()
    if not result.ok:
        return AdminView(page, Routes.ADMIN_SETTINGS, "Settings", Alert(result.error_kind, result.message))

    values = result.data
    notice = ft.Column(spacing=Spacing.SM)
    fields = {
        "BORROWING_LIMIT": admin_text_field(label="Borrowing limit", value=str(values.get("BORROWING_LIMIT", 3)), keyboard_type=ft.KeyboardType.NUMBER, col={"sm": 12, "md": 6, "lg": 3}),
        "BORROWING_PERIOD_DAYS": admin_text_field(label="Borrowing period (days)", value=str(values.get("BORROWING_PERIOD_DAYS", 7)), keyboard_type=ft.KeyboardType.NUMBER, col={"sm": 12, "md": 6, "lg": 3}),
        "MAX_RENEWALS": admin_text_field(label="Maximum renewals", value=str(values.get("MAX_RENEWALS", 1)), keyboard_type=ft.KeyboardType.NUMBER, col={"sm": 12, "md": 6, "lg": 3}),
        "RESERVATION_HOLD_DAYS": admin_text_field(label="Reservation hold (days)", value=str(values.get("RESERVATION_HOLD_DAYS", 2)), keyboard_type=ft.KeyboardType.NUMBER, col={"sm": 12, "md": 6, "lg": 3}),
    }
    overdue = ft.Switch(label="Allow borrowing when a user has overdue items", value=str(values.get("ALLOW_BORROW_WITH_OVERDUE", "false")).lower() == "true")

    def save(_event) -> None:
        if save_button.disabled:
            return
        invalid = []
        for key, field in fields.items():
            raw = str(field.value or "").strip()
            minimum = 0 if key == "MAX_RENEWALS" else 1
            if not raw.isdigit() or int(raw) < minimum:
                invalid.append(str(field.label))
        if invalid:
            notice.controls = [Alert("validation_error", "Enter valid whole numbers for: " + ", ".join(invalid), title="Check policy values")]
            page.update()
            return
        set_button_loading(save_button, True, "Save policies", "Saving…")
        notice.controls = []
        page.update()
        updates = {key: field.value for key, field in fields.items()}
        updates["ALLOW_BORROW_WITH_OVERDUE"] = "true" if overdue.value else "false"
        response = admin_service.update_settings(updates)
        if not response.ok:
            set_button_loading(save_button, False, "Save policies")
            notice.controls = [Alert(response.error_kind, response.message, title="Settings not saved")]
            page.update()
            return
        set_button_loading(save_button, False, "Save policies")
        notice.controls = [Alert("success", "Library policies were updated successfully.")]
        page.update()

    save_button = ft.FilledButton("Save policies", icon=ft.Icons.SAVE_ROUNDED, on_click=save)
    policy_panel = section_card(
        title="Circulation policies",
        subtitle="These rules are authoritative and enforced by the backend for every borrowing transaction.",
        content=ft.Column(
            spacing=Spacing.LG,
            controls=[
                ft.ResponsiveRow(spacing=Spacing.MD, run_spacing=Spacing.MD, controls=list(fields.values())),
                ft.Container(bgcolor=Colors.SURFACE_ALT, border=ft.border.all(1, Colors.BORDER), border_radius=Radius.MD, padding=Spacing.MD, content=overdue),
                notice,
                ft.Row(alignment=ft.MainAxisAlignment.END, controls=[save_button]),
            ],
        ),
    )
    connection_panel = section_card(
        title="Workstation connection",
        subtitle="Read-only connection information for this administration workstation.",
        content=ft.Column(
            spacing=Spacing.MD,
            controls=[
                admin_text_field(label="Backend API URL", value=settings.api_base_url, read_only=True),
                ft.ResponsiveRow(
                    spacing=Spacing.MD,
                    controls=[
                        ft.Container(col={"sm": 12, "md": 6}, bgcolor=Colors.SURFACE_ALT, border_radius=Radius.MD, padding=Spacing.MD, content=ft.Row(controls=[ft.Icon(ft.Icons.TIMER_OUTLINED, color=Colors.PRIMARY), ft.Column(tight=True, spacing=2, controls=[ft.Text("Request timeout", size=11, color=Colors.TEXT_SECONDARY), ft.Text(f"{settings.api_timeout_seconds} seconds", weight=ft.FontWeight.W_600)])])),
                        ft.Container(col={"sm": 12, "md": 6}, bgcolor=Colors.SUCCESS_BG, border_radius=Radius.MD, padding=Spacing.MD, content=ft.Row(controls=[ft.Icon(ft.Icons.VERIFIED_OUTLINED, color=Colors.SUCCESS), ft.Column(tight=True, spacing=2, controls=[ft.Text("Demo fallback", size=11, color=Colors.SUCCESS), ft.Text("Disabled · Live data only", weight=ft.FontWeight.W_600, color=Colors.SUCCESS)])])),
                    ],
                ),
            ],
        ),
    )
    content = ft.Column(tight=True, spacing=Spacing.LG, controls=[policy_panel, connection_panel])
    return AdminView(page, Routes.ADMIN_SETTINGS, "Settings", content, subtitle="Library policies and workstation configuration")
