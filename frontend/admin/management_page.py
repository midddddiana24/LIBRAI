"""Reusable, polished administrative list for circulation records."""

from __future__ import annotations

import asyncio
import flet as ft

from components.admin_ui import admin_search_field, admin_text_field, form_section, page_intro, section_card, status_badge
from components.alert import Alert
from components.empty_state import EmptyState
from components.loading_view import InlineLoading, set_button_loading
from components.sidebar import AdminView
from core.theme import Colors, Radius, Spacing
from services.management_service import management_service
from utils.formatting import format_date


def build(page, route, title, endpoint, description, allow_add=False):
    results = ft.Column(spacing=Spacing.SM, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    notice = ft.Column(spacing=Spacing.SM)
    search = admin_search_field(hint_text=f"Search {title.lower()}…", expand=True)
    count_text = ft.Text("", size=11, color=Colors.TEXT_SECONDARY)
    page_index = 0
    page_size = 25

    def circulation_summary(row: dict) -> tuple[str, str, str, str]:
        user_name = str(row.get("user_name") or row.get("user") or "Unknown user")
        student_id = str(row.get("student_id") or "No student number")
        if endpoint == "/borrowings":
            return (str(row.get("book_title") or "Untitled book"), f"Borrowed by {user_name} ({student_id})", f"{row.get('transaction_id', 'Borrowing')}  •  Borrowed {format_date(row.get('borrowed_at'))}  •  Due {format_date(row.get('due_at'))}", ft.Icons.MENU_BOOK_OUTLINED)
        if endpoint == "/returns":
            return (str(row.get("book") or row.get("book_title") or "Untitled book"), f"Returned by {user_name} ({student_id})", f"Returned {format_date(row.get('returned_at'))}", ft.Icons.KEYBOARD_RETURN_ROUNDED)
        if endpoint == "/reservations":
            return (str(row.get("book_title") or "Untitled book"), f"Reserved by {user_name} ({student_id})", f"Queue position {row.get('position') or '—'}  •  Reserved {format_date(row.get('reserved_at'))}", ft.Icons.BOOKMARK_BORDER_ROUNDED)
        return (str(row.get("title") or row.get("name") or f"Record {row.get('id', '')}"), "", "", ft.Icons.RECEIPT_LONG_OUTLINED)

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
        if hasattr(page, "run_task"):
            page.run_task(load_async, show_loading)
        else:  # lightweight route-test page
            load_async_sync_for_test(show_loading)

    async def load_async(show_loading: bool = True) -> None:
        nonlocal page_index
        # The page must be attached before an async result can update its
        # controls. Starting immediately during build can leave the initial
        # loading surface visible forever when the API responds very quickly.
        await asyncio.sleep(0.05)
        if show_loading:
            results.controls = [InlineLoading(f"Loading {title.lower()}…")]
            page.update()
        try:
            response = await asyncio.to_thread(
                management_service.list,
                endpoint,
                str(search.value or "").strip() or None,
                page_index * page_size,
                page_size,
            )
        except Exception as exc:
            results.controls = [Alert("server_error", f"Could not load {title.lower()}: {exc}", title="Loading failed")]
            page.update()
            return
        results.controls.clear()
        if not response.ok:
            count_text.value = "Unable to load records"
            results.controls.append(Alert(response.error_kind, response.message))
        else:
            rows = response.data.get("items", []) if isinstance(response.data, dict) else response.data
            rows = rows if isinstance(rows, list) else []
            rows = [row if isinstance(row, dict) else {"value": row} for row in rows]
            if search.value:
                needle = str(search.value).strip().lower()
                rows = [row for row in rows if needle in " ".join(str(value).lower() for value in row.values())]
            count_text.value = f"{len(rows):,} record{'s' if len(rows) != 1 else ''} · Live data"
            if not rows:
                results.controls.append(EmptyState(f"No {title.lower()} found", description))
            for row in rows:
                if not isinstance(row, dict):
                    row = {"value": row}
                primary, person_line, detail_line, record_icon = circulation_summary(row)
                status = row.get("status")
                secondary_values = []
                results.controls.append(
                    ft.Container(
                        bgcolor=Colors.SURFACE,
                        border=ft.border.all(1, Colors.BORDER),
                        border_radius=Radius.XL,
                        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=14),
                        content=ft.Row(
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(width=42, height=42, border_radius=Radius.MD, bgcolor=Colors.PRIMARY_MUTED, alignment=ft.alignment.center, content=ft.Icon(record_icon, size=19, color=Colors.PRIMARY)),
                                ft.Container(
                                    expand=True,
                                    content=ft.Column(
                                        tight=True,
                                        spacing=3,
                                        controls=[
                                            ft.Text(str(primary), size=13, weight=ft.FontWeight.W_700),
                                            ft.Text(person_line, size=12, color=Colors.TEXT_PRIMARY, max_lines=1),
                                            ft.Text(detail_line, size=11, color=Colors.TEXT_SECONDARY, max_lines=1),
                                            ft.Text(" · ".join(secondary_values), size=11, color=Colors.TEXT_SECONDARY, max_lines=2),
                                        ],
                                    ),
                                ),
                                *([status_badge(status)] if status else []),
                                ft.IconButton(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, icon_size=14, tooltip="View details", on_click=lambda _event, item=row: show_details(item)),
                            ],
                        ),
                    )
                )
        page.update()

    def load_async_sync_for_test(show_loading: bool = True) -> None:
        """Keep constructor smoke tests usable without a Flet event loop."""
        if show_loading:
            results.controls = [InlineLoading(f"Loading {title.lower()}â€¦")]

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

    previous_button = ft.IconButton(ft.Icons.CHEVRON_LEFT_ROUNDED, tooltip="Previous page")
    next_button = ft.IconButton(ft.Icons.CHEVRON_RIGHT_ROUNDED, tooltip="Next page")

    def previous_page(_event):
        nonlocal page_index
        if page_index > 0:
            page_index -= 1
            load()

    def next_page(_event):
        nonlocal page_index
        page_index += 1
        load()

    previous_button.on_click = previous_page
    next_button.on_click = next_page
    search.on_submit = load
    # Keep the search field in the same non-wrapping toolbar pattern used by
    # Books and Library Users. An expanded row inside a wrapping row makes
    # Flet stretch the field vertically, producing the large gray block.
    toolbar = section_card(
        ft.Row(
            spacing=Spacing.SM,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(expand=True, content=search),
                ft.OutlinedButton("Refresh", icon=ft.Icons.REFRESH_ROUNDED, on_click=load),
                *([ft.FilledButton(f"Add {title.rstrip('s')}", icon=ft.Icons.ADD_ROUNDED, on_click=open_form)] if allow_add else []),
            ],
        ),
        padding=Spacing.MD,
    )
    results.controls = [InlineLoading(f"Loading {title.lower()}â€¦")]
    pager = ft.Row(controls=[previous_button, next_button])
    content = ft.Column(tight=True, spacing=Spacing.LG, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, controls=[toolbar, ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(f"{title} records", size=16, weight=ft.FontWeight.W_700), ft.Row(controls=[count_text, pager])]), notice, results])
    view = AdminView(page, route, title, content, subtitle=description)
    if hasattr(page, "run_task"):
        page.run_task(load_async, False)
    return view
