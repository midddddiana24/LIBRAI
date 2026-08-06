"""Reusable, polished administrative list for circulation records."""

from __future__ import annotations

import flet as ft

from components.admin_ui import admin_search_field, admin_text_field, form_section, page_intro, section_card, status_badge
from components.alert import Alert
from components.empty_state import EmptyState
from components.loading_view import InlineLoading, set_button_loading
from components.sidebar import AdminView
from core.theme import Colors, Radius, Spacing
from services.management_service import management_service


def build(page, route, title, endpoint, description, allow_add=False):
    results = ft.Column(spacing=Spacing.SM, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    notice = ft.Column(spacing=Spacing.SM)
    search = admin_search_field(hint_text=f"Search {title.lower()}…", expand=True)
    count_text = ft.Text("", size=11, color=Colors.TEXT_SECONDARY)

    def show_details(row: dict) -> None:
        detail_rows = [
            ft.Container(
                padding=ft.padding.symmetric(vertical=9),
                border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)),
                content=ft.ResponsiveRow(
                    controls=[
                        ft.Text(str(key).replace("_", " ").title(), col={"sm": 12, "md": 4}, size=11, weight=ft.FontWeight.W_600, color=Colors.TEXT_SECONDARY),
                        ft.Text(str(value), col={"sm": 12, "md": 8}, selectable=True, size=12, color=Colors.TEXT_PRIMARY),
                    ]
                ),
            )
            for key, value in row.items()
        ]
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Record details"),
            content=ft.Container(width=600, height=470, content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0, controls=detail_rows)),
            actions=[ft.FilledButton("Done", on_click=lambda _event: page.close(dialog))],
        )
        page.open(dialog)

    def load(_event=None, show_loading: bool = True) -> None:
        if show_loading:
            results.controls = [InlineLoading(f"Loading {title.lower()}…")]
            page.update()
        response = management_service.list(endpoint, str(search.value or "").strip() or None)
        results.controls.clear()
        if not response.ok:
            count_text.value = "Unable to load records"
            results.controls.append(Alert(response.error_kind, response.message))
        else:
            rows = response.data.get("items", []) if isinstance(response.data, dict) else response.data
            if search.value:
                needle = str(search.value).strip().lower()
                rows = [row for row in rows if needle in " ".join(str(value).lower() for value in row.values())]
            count_text.value = f"{len(rows):,} record{'s' if len(rows) != 1 else ''} · Live data"
            if not rows:
                results.controls.append(EmptyState(f"No {title.lower()} found", description))
            for row in rows:
                primary = row.get("title") or row.get("name") or row.get("book") or row.get("action") or f"Record {row.get('id', '')}"
                status = row.get("status")
                secondary_values = [str(value) for key, value in row.items() if key not in {"id", "title", "name", "book", "action", "status"} and value is not None]
                results.controls.append(
                    ft.Container(
                        bgcolor=Colors.SURFACE,
                        border=ft.border.all(1, Colors.BORDER),
                        border_radius=Radius.XL,
                        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.MD),
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=38, height=38, border_radius=Radius.MD, bgcolor=Colors.PRIMARY_MUTED, alignment=ft.alignment.center, content=ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=18, color=Colors.PRIMARY)),
                                ft.Column(expand=True, tight=True, spacing=3, controls=[ft.Text(str(primary), size=13, weight=ft.FontWeight.W_700), ft.Text(" · ".join(secondary_values), size=11, color=Colors.TEXT_SECONDARY, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)]),
                                *([status_badge(status)] if status else []),
                                ft.IconButton(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, icon_size=14, tooltip="View details", on_click=lambda _event, item=row: show_details(item)),
                            ],
                        ),
                    )
                )
        page.update()

    def open_form(_event) -> None:
        specs = ([('isbn','ISBN'),('title','Title'),('author','Author'),('publisher','Publisher'),('publication_year','Publication year'),('category','Category'),('shelf_location','Shelf location')] if endpoint == "/books" else [('student_id','Student number'),('first_name','First name'),('last_name','Last name'),('course','Course'),('year_level','Year level'),('email','Email')])
        fields = {key: admin_text_field(label=label, col={"sm": 12, "md": 6}) for key, label in specs}
        form_notice = ft.Column()

        def save(_event) -> None:
            if save_button.disabled:
                return
            required = {"isbn", "title", "author", "category", "shelf_location"} if endpoint == "/books" else {"student_id", "first_name", "last_name", "course", "year_level"}
            missing = [str(fields[key].label) for key in required if not str(fields[key].value or "").strip()]
            if missing:
                form_notice.controls = [Alert("validation_error", "Complete: " + ", ".join(missing), title="Required fields")]
                page.update()
                return
            payload = {key: str(control.value or "").strip() for key, control in fields.items() if str(control.value or "").strip()}
            if payload.get("publication_year"):
                if not payload["publication_year"].isdigit():
                    form_notice.controls = [Alert("validation_error", "Publication year must be a number.")]
                    page.update()
                    return
                payload["publication_year"] = int(payload["publication_year"])
            set_button_loading(save_button, True, "Save", "Saving…")
            page.update()
            response = management_service.create(endpoint, payload)
            if response.ok:
                page.close(dialog)
                load()
            else:
                set_button_loading(save_button, False, "Save")
                form_notice.controls = [Alert(response.error_kind, response.message, title="Could not save")]
                page.update()

        save_button = ft.FilledButton("Save", icon=ft.Icons.SAVE_ROUNDED, on_click=save)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Add {title.rstrip('s')}"),
            content=ft.Container(width=620, content=ft.Column(tight=True, spacing=Spacing.MD, controls=[form_section("Record information", "Complete the required administrative details.", list(fields.values())), form_notice])),
            actions=[ft.TextButton("Cancel", on_click=lambda _event: page.close(dialog)), save_button],
        )
        page.open(dialog)

    search.on_submit = load
    toolbar = section_card(
        ft.Row(
            wrap=True,
            spacing=Spacing.SM,
            run_spacing=Spacing.SM,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(expand=True, spacing=Spacing.SM, controls=[search, ft.OutlinedButton("Refresh", icon=ft.Icons.REFRESH_ROUNDED, on_click=load)]),
                *([ft.FilledButton(f"Add {title.rstrip('s')}", icon=ft.Icons.ADD_ROUNDED, on_click=open_form)] if allow_add else []),
            ],
        ),
        padding=Spacing.MD,
    )
    load(show_loading=False)
    content = ft.Column(tight=True, spacing=Spacing.LG, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, controls=[toolbar, ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(f"{title} records", size=16, weight=ft.FontWeight.W_700), count_text]), notice, results])
    return AdminView(page, route, title, content, subtitle=description)
