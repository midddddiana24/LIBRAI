"""Administrative report preview and export workspace."""

from __future__ import annotations

import flet as ft

from components.admin_ui import admin_dropdown, admin_text_field, section_card, table_shell
from components.alert import Alert
from components.empty_state import EmptyState
from components.loading_view import InlineLoading, set_button_loading
from components.sidebar import AdminView
from core.constants import Routes
from core.theme import Colors, Spacing
from services.admin_service import admin_service


REPORTS = [
    ("daily_borrowing", "Daily borrowing"),
    ("weekly_borrowing", "Weekly borrowing"),
    ("monthly_borrowing", "Monthly borrowing"),
    ("overdue", "Overdue books"),
    ("inventory", "Inventory"),
    ("most_borrowed", "Most borrowed books"),
    ("popular_categories", "Popular categories"),
    ("user_activity", "User activity"),
]


def build(page: ft.Page) -> ft.View:
    report = admin_dropdown(label="Report", col={"sm": 12, "md": 6, "lg": 4}, value="daily_borrowing", options=[ft.dropdown.Option(key, label) for key, label in REPORTS])
    start = admin_text_field(label="Start date", hint_text="YYYY-MM-DD", col={"sm": 12, "md": 6, "lg": 3})
    end = admin_text_field(label="End date", hint_text="YYYY-MM-DD", col={"sm": 12, "md": 6, "lg": 3})
    format_ = admin_dropdown(label="Format", col={"sm": 12, "md": 6, "lg": 2}, value="pdf", options=[ft.dropdown.Option(value, value.upper()) for value in ["pdf", "csv", "xlsx"]])
    notice = ft.Column(spacing=Spacing.SM)
    download_button = ft.FilledButton("Download generated file", icon=ft.Icons.DOWNLOAD_DONE_ROUNDED, visible=False)
    preview_body = ft.Column(spacing=Spacing.MD)
    preview_summary = ft.Text("", size=12, color=Colors.TEXT_SECONDARY)

    def load_preview(_event=None, update: bool = True) -> None:
        if update:
            preview_body.controls = [InlineLoading("Preparing report preview…")]
            page.update()
        result = admin_service.report_list(report_type=report.value, start_date=start.value or None, end_date=end.value or None)
        preview_body.controls.clear()
        if not result.ok:
            preview_summary.value = "Preview unavailable"
            preview_body.controls.append(Alert(result.error_kind, result.message))
        else:
            payload = result.data if isinstance(result.data, dict) else {"items": result.data}
            rows = payload.get("items", [])
            headers = payload.get("headers", [])
            preview_summary.value = f"{int(payload.get('total', len(rows))):,} records · showing up to 25"
            if not rows or not headers:
                preview_body.controls.append(EmptyState("No report data", "Transactions matching this report will appear here.", ft.Icons.DESCRIPTION_OUTLINED))
            else:
                table = ft.DataTable(
                    columns=[ft.DataColumn(ft.Text(str(header).replace("_", " ").title())) for header in headers],
                    rows=[ft.DataRow(cells=[ft.DataCell(ft.Text(str(row.get(header, "—")), max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)) for header in headers]) for row in rows[:25]],
                )
                preview_body.controls.append(table_shell(table))
        if update:
            page.update()

    def export(_event) -> None:
        if export_button.disabled:
            return
        set_button_loading(export_button, True, "Export report", "Generating…")
        download_button.visible = False
        page.update()
        result = admin_service.export_report({"report_type": report.value, "start_date": start.value or None, "end_date": end.value or None, "format": str(format_.value).lower()})
        set_button_loading(export_button, False, "Export report")
        if result.ok:
            notice.controls = [Alert("success", "Report generated successfully. The secure download is ready for five minutes.")]
            download_button.visible = True
            download_button.on_click = lambda _event: page.launch_url(result.data["download_url"])
        else:
            notice.controls = [Alert(result.error_kind, result.message)]
        page.update()

    export_button = ft.FilledButton("Export report", icon=ft.Icons.DOWNLOAD_ROUNDED, on_click=export)
    report.on_change = load_preview
    start.on_submit = load_preview
    end.on_submit = load_preview
    load_preview(update=False)
    generator = section_card(
        ft.Column(
            spacing=Spacing.MD,
            controls=[
                ft.Text("Generate report", size=18, weight=ft.FontWeight.W_600),
                ft.Text("Select a report, review the live preview, then request a backend-generated export.", size=13, color=Colors.TEXT_SECONDARY),
                ft.ResponsiveRow(spacing=12, run_spacing=12, controls=[report, start, end, format_]),
                ft.Row(wrap=True, alignment=ft.MainAxisAlignment.END, controls=[ft.OutlinedButton("Refresh preview", icon=ft.Icons.REFRESH_ROUNDED, on_click=load_preview), export_button]),
                notice,
                ft.Row(alignment=ft.MainAxisAlignment.END, controls=[download_button]),
            ],
        )
    )
    preview = section_card(
        ft.Column(spacing=Spacing.MD, controls=[preview_summary, preview_body]),
        title="Report preview",
        subtitle="Live backend data matching the selected report and date range.",
    )
    return AdminView(page, Routes.ADMIN_REPORTS, "Reports", ft.Column(tight=True, spacing=Spacing.LG, controls=[generator, preview]), subtitle="Preview and export official library reports")
