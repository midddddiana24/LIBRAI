"""Administrative library-member management view."""

from __future__ import annotations

import flet as ft

from components.admin_ui import admin_dropdown, admin_search_field, admin_text_field, confirmation_dialog, form_section, page_intro, qr_dialog, section_card, status_badge, table_shell
from components.alert import Alert
from components.empty_state import EmptyState
from components.loading_view import InlineLoading, set_button_loading
from components.image_picker import ImagePickerControl
from components.sidebar import AdminView
from core.constants import Routes
from core.theme import Colors, Spacing
from services.admin_catalog_service import admin_catalog_service


PAGE_SIZE = 25
USER_STATUSES = ["ACTIVE", "INACTIVE", "SUSPENDED"]


def build(page: ft.Page) -> ft.View:
    state = {"offset": 0, "total": 0}
    viewport = float(getattr(page, "width", None) or 1366)
    available_table_width = min(1560.0, max(900.0, viewport - (280 if viewport >= 1060 else 48)))
    table_scale = min(1.45, max(0.85, available_table_width / 1070.0))
    table_width = lambda base: int(base * table_scale)
    search = admin_search_field(hint_text="Search student number or name")
    notice = ft.Column(spacing=Spacing.SM)
    body = ft.Column(spacing=Spacing.MD, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    pager = ft.Row(alignment=ft.MainAxisAlignment.END, spacing=Spacing.SM)

    def show_notice(kind: str, message: str, title: str | None = None) -> None:
        notice.controls = [Alert(kind, message, title=title)]
        page.update()

    def open_user_form(user: dict | None = None) -> None:
        creating = user is None
        source = user or {}
        student_id = admin_text_field(label="Student number", value=str(source.get("student_id") or ""), disabled=not creating, col={"sm":12,"md":6})
        first_name = admin_text_field(label="First name", value=str(source.get("first_name") or ""), col={"sm":12,"md":6})
        last_name = admin_text_field(label="Last name", value=str(source.get("last_name") or ""), col={"sm":12,"md":6})
        course = admin_text_field(label="Course / program", value=str(source.get("course") or ""), col={"sm":12,"md":8})
        year_level = admin_text_field(label="Year level", value=str(source.get("year_level") or ""), col={"sm":12,"md":4})
        email = admin_text_field(label="Email", value=str(source.get("email") or ""), keyboard_type=ft.KeyboardType.EMAIL, col={"sm":12,"md":6})
        contact = admin_text_field(label="Contact number", value=str(source.get("contact_number") or ""), col={"sm":12,"md":6})
        status = admin_dropdown(label="Account status", value=str(source.get("status") or "ACTIVE").upper(), options=[ft.dropdown.Option(x) for x in USER_STATUSES], col=12)
        form_notice = ft.Column()
        photo_picker = ImagePickerControl(page, "User profile photo", source.get("photo_url"), purpose="user_photo")

        def close_form() -> None:
            photo_picker.cleanup()
            if photo_picker.picker in page.overlay:
                page.overlay.remove(photo_picker.picker)
            page.close(dialog)

        def save(_event) -> None:
            if save_button.disabled:
                return
            required = [student_id, first_name, last_name, course, year_level]
            missing = [str(field.label) for field in required if not str(field.value or "").strip()]
            if missing:
                form_notice.controls = [Alert("validation_error", "Complete: " + ", ".join(missing), "Required fields")]
                page.update()
                return
            set_button_loading(save_button, True, "Save user", "Saving…")
            page.update()
            payload = {
                "first_name": str(first_name.value).strip(),
                "last_name": str(last_name.value).strip(),
                "course": str(course.value).strip(),
                "year_level": str(year_level.value).strip(),
                "email": str(email.value or "").strip() or None,
                "contact_number": str(contact.value or "").strip() or None,
                "status": str(status.value),
            }
            if creating:
                payload["student_id"] = str(student_id.value).strip()
            result = admin_catalog_service.create_user(payload) if creating else admin_catalog_service.update_user(int(source["id"]), payload)
            if not result.ok:
                form_notice.controls = [Alert(result.error_kind, result.message, "User was not saved")]
                set_button_loading(save_button, False, "Save user")
                page.update()
                return
            image_warning = None
            if photo_picker.selected_path:
                set_button_loading(save_button, True, "Save user", "Uploading photo…")
                page.update()
                uploaded = admin_catalog_service.upload_user_photo(int(result.data["id"]), str(photo_picker.selected_path))
                if not uploaded.ok:
                    image_warning = uploaded.message
            close_form()
            if image_warning:
                show_notice("validation_error", f"The user was saved, but the photo was not uploaded: {image_warning}", "Photo upload incomplete")
            else:
                show_notice("success", "Library user registered." if creating else "Library user updated.")
            load()

        save_button = ft.FilledButton("Save user", icon=ft.Icons.SAVE_ROUNDED, on_click=save)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Register library user" if creating else "Edit library user"),
            content=ft.Container(
                width=590,
                height=510,
                content=ft.Column(
                    scroll=ft.ScrollMode.AUTO,
                    spacing=18,
                    controls=[
                        form_section("Student identity","Official details used to identify the library account.",[student_id,first_name,last_name]),
                        photo_picker.control,
                        ft.Divider(height=1,color=Colors.BORDER),
                        form_section("Academic information","Program and year details shown during kiosk verification.",[course,year_level]),
                        ft.Divider(height=1,color=Colors.BORDER),
                        form_section("Contact and account","Contact information is visible only to authorized staff.",[email,contact,status]),
                        form_notice,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _e: close_form()),
                save_button,
            ],
        )
        page.open(dialog)

    def rotate_user_qr(user: dict) -> None:
        def confirm(_event, dialog) -> None:
            result = admin_catalog_service.rotate_user_qr(int(user["id"]))
            page.close(dialog)
            if result.ok:
                qr_dialog(page, "Library user QR", result.data["qr_image"], str(user.get("student_id", "")), replaced=True, download_url=result.data.get("download_url"))
            else:
                show_notice(result.error_kind, result.message)

        confirmation_dialog(
            page,
            "Replace user QR code?",
            "The previously issued user QR will stop working immediately.",
            "Replace QR",
            confirm,
        )

    def view_user_qr(user: dict) -> None:
        result = admin_catalog_service.get_user_qr(int(user["id"]))
        if result.ok:
            qr_dialog(page, "Library user QR", result.data["qr_image"], str(user.get("student_id", "")), download_url=result.data.get("download_url"))
        else:
            show_notice(result.error_kind, result.message)

    def show_history(user: dict) -> None:
        result = admin_catalog_service.user_borrowings(int(user["id"]))
        if not result.ok:
            show_notice(result.error_kind, result.message, "History unavailable")
            return
        payload = result.data if isinstance(result.data, dict) else {"items": result.data}
        items = payload.get("items", [])
        history = ft.Column(spacing=Spacing.SM, scroll=ft.ScrollMode.AUTO)
        if not items:
            history.controls.append(EmptyState("No borrowing history", "This user has no recorded transactions."))
        else:
            for item in items:
                history.controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(vertical=10),
                        border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    expand=True,
                                    tight=True,
                                    controls=[
                                        ft.Text(str(item.get("book_title", "Unknown book")), weight=ft.FontWeight.W_600),
                                        ft.Text(f"Borrowed: {str(item.get('borrowed_at', ''))[:10]}  •  Due: {str(item.get('due_at', ''))[:10]}", size=12, color=Colors.TEXT_SECONDARY),
                                    ],
                                ),
                                status_badge(item.get("status")),
                            ],
                        ),
                    )
                )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Borrowing history — {user.get('display_name') or user.get('name', '')}"),
            content=ft.Container(width=650, height=460, content=history),
            actions=[ft.FilledButton("Done", on_click=lambda _e: page.close(dialog))],
        )
        page.open(dialog)

    def actions(user: dict) -> ft.PopupMenuButton:
        return ft.PopupMenuButton(
            icon=ft.Icons.MORE_HORIZ_ROUNDED,
            tooltip="User actions",
            items=[
                ft.PopupMenuItem(content="Edit user", icon=ft.Icons.EDIT_OUTLINED, on_click=lambda _e: open_user_form(user)),
                ft.PopupMenuItem(content="Borrowing history", icon=ft.Icons.HISTORY_ROUNDED, on_click=lambda _e: show_history(user)),
                ft.PopupMenuItem(content="View QR", icon=ft.Icons.QR_CODE_2_ROUNDED, on_click=lambda _e: view_user_qr(user)),
                ft.PopupMenuItem(content="Replace QR", icon=ft.Icons.REFRESH_ROUNDED, on_click=lambda _e: rotate_user_qr(user)),
            ],
        )

    def load(_event=None, show_loading: bool = True) -> None:
        if show_loading:
            body.controls = [InlineLoading("Loading library users…")]
            page.update()
        result = admin_catalog_service.list_users(str(search.value or "").strip() or None, state["offset"], PAGE_SIZE)
        body.controls.clear()
        if not result.ok:
            body.controls.append(Alert(result.error_kind, result.message))
            page.update()
            return
        payload = result.data if isinstance(result.data, dict) else {"items": result.data, "total": len(result.data)}
        rows = payload.get("items", [])
        state["total"] = int(payload.get("total", len(rows)))
        if not rows:
            body.controls.append(EmptyState("No library users found", "Change the search or register a new user.", ft.Icons.PERSON_SEARCH_ROUNDED))
        else:
            table = ft.DataTable(
                heading_row_color="#F8FAFC",
                column_spacing=table_width(24),
                horizontal_margin=20,
                columns=[ft.DataColumn(ft.Text(x, weight=ft.FontWeight.W_600)) for x in ["User", "Student no.", "Course", "Borrowed", "Overdue", "Status", ""]],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Container(width=table_width(260), content=ft.Row(controls=[ft.Container(width=36,height=36,border_radius=99,clip_behavior=ft.ClipBehavior.ANTI_ALIAS,bgcolor=Colors.PRIMARY_MUTED,alignment=ft.alignment.center,content=ft.Image(src=user.get("photo_url"),fit=ft.ImageFit.COVER) if user.get("photo_url") else ft.Icon(ft.Icons.PERSON_OUTLINE_ROUNDED,size=18,color=Colors.PRIMARY)),ft.Column(expand=True, tight=True, spacing=1, controls=[ft.Text(str(user.get("display_name") or user.get("name", "")), weight=ft.FontWeight.W_600, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(str(user.get("email") or "No email"), size=11, color=Colors.TEXT_SECONDARY, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)])]))),
                            ft.DataCell(ft.Text(str(user.get("student_id", "")), width=table_width(120))),
                            ft.DataCell(ft.Container(width=table_width(200), content=ft.Column(tight=True, spacing=1, controls=[ft.Text(str(user.get("course", "")), max_lines=1, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(str(user.get("year_level", "")), size=11, color=Colors.TEXT_SECONDARY)]))),
                            ft.DataCell(ft.Container(width=table_width(80), content=ft.Text(str(user.get("active_borrowing_count", 0))))),
                            ft.DataCell(ft.Container(width=table_width(80), content=ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=Colors.ERROR if user.get("has_overdue_books") else Colors.TEXT_DISABLED, size=20))),
                            ft.DataCell(ft.Container(width=table_width(95), alignment=ft.alignment.center_left, content=status_badge(user.get("status")))),
                            ft.DataCell(ft.Container(width=table_width(44), alignment=ft.alignment.center, content=actions(user))),
                        ]
                    )
                    for user in rows
                ],
            )
            body.controls.append(table_shell(table))
        start = state["offset"] + 1 if state["total"] else 0
        end = min(state["offset"] + PAGE_SIZE, state["total"])
        pager.controls = [
            ft.Text(f"{start}–{end} of {state['total']}", color=Colors.TEXT_SECONDARY),
            ft.IconButton(ft.Icons.CHEVRON_LEFT_ROUNDED, disabled=state["offset"] == 0, on_click=previous),
            ft.IconButton(ft.Icons.CHEVRON_RIGHT_ROUNDED, disabled=state["offset"] + PAGE_SIZE >= state["total"], on_click=next_page),
        ]
        page.update()

    def previous(_event) -> None:
        state["offset"] = max(0, state["offset"] - PAGE_SIZE)
        load()

    def next_page(_event) -> None:
        state["offset"] += PAGE_SIZE
        load()

    def new_search(_event=None) -> None:
        state["offset"] = 0
        load()

    search.on_submit = new_search
    toolbar = ft.Row(
        spacing=Spacing.SM,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(expand=True, content=search),
            ft.OutlinedButton("Refresh", icon=ft.Icons.REFRESH_ROUNDED, on_click=new_search),
            ft.FilledButton("Register user", icon=ft.Icons.PERSON_ADD_ROUNDED, on_click=lambda _e: open_user_form()),
        ],
    )
    load(show_loading=False)
    content = ft.Column(tight=True, spacing=Spacing.LG, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, controls=[section_card(toolbar, padding=Spacing.MD), notice, body, pager])
    return AdminView(page, Routes.ADMIN_USERS, "Library users", content, subtitle="Manage accounts, eligibility, history, and secure QR identities")
