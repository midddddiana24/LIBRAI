"""Professional catalog-title and physical-copy management view."""

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
COPY_STATUSES = ["AVAILABLE", "LOST", "DAMAGED", "ARCHIVED"]


def build(page: ft.Page) -> ft.View:
    state = {"offset": 0, "total": 0}
    viewport = float(getattr(page, "width", None) or 1366)
    available_table_width = min(1560.0, max(900.0, viewport - (280 if viewport >= 1060 else 48)))
    table_scale = min(1.45, max(0.85, available_table_width / 1070.0))
    table_width = lambda base: int(base * table_scale)
    search = admin_search_field(hint_text="Search title, author, ISBN, or keyword")
    include_archived = ft.Checkbox(label="Include archived", value=False)
    category_filter = admin_text_field(label="Category", hint_text="Technology", width=145)
    author_filter = admin_text_field(label="Author", hint_text="Any author", width=145)
    shelf_filter = admin_text_field(label="Shelf", hint_text="A-01", width=110)
    available_filter = ft.Checkbox(label="Available only", value=False)
    notice = ft.Column(spacing=Spacing.SM)
    body = ft.Column(spacing=Spacing.MD, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    pager = ft.Row(alignment=ft.MainAxisAlignment.END, spacing=Spacing.SM)
    csv_picker = ft.FilePicker()
    page.overlay.append(csv_picker)

    def show_notice(kind: str, message: str, title: str | None = None) -> None:
        notice.controls = [Alert(kind, message, title=title)]
        page.update()

    def book_payload(fields: dict[str, ft.Control], creating: bool) -> dict | None:
        required = ["isbn", "title", "author", "category", "shelf_location"]
        missing = [str(fields[key].label) for key in required if not str(fields[key].value or "").strip()]
        if missing:
            show_notice("validation_error", "Complete: " + ", ".join(missing), "Required fields")
            return None
        year = str(fields["publication_year"].value or "").strip()
        if year and (not year.isdigit() or not 1000 <= int(year) <= 2200):
            show_notice("validation_error", "Publication year must be between 1000 and 2200.")
            return None
        payload = {
            "isbn": str(fields["isbn"].value).strip(),
            "title": str(fields["title"].value).strip(),
            "author": str(fields["author"].value).strip(),
            "publisher": str(fields["publisher"].value or "").strip() or None,
            "publication_year": int(year) if year else None,
            "category": str(fields["category"].value).strip(),
            "shelf_location": str(fields["shelf_location"].value).strip(),
            "description": str(fields["description"].value or "").strip() or None,
            "keywords": [x.strip() for x in str(fields["keywords"].value or "").split(",") if x.strip()],
            "subjects": [x.strip() for x in str(fields["subjects"].value or "").split(",") if x.strip()],
        }
        if creating:
            initial_copies = str(fields["initial_copy_count"].value or "").strip()
            if not initial_copies.isdigit() or not 0 <= int(initial_copies) <= 100:
                show_notice("validation_error", "Initial physical copies must be between 0 and 100.")
                return None
            payload["initial_copy_count"] = int(initial_copies)
        return payload

    def open_book_form(book: dict | None = None) -> None:
        creating = book is None
        source = book or {}
        fields: dict[str, ft.Control] = {
            "isbn": admin_text_field(label="ISBN", value=str(source.get("isbn") or ""), col={"sm":12,"md":6}),
            "title": admin_text_field(label="Title", value=str(source.get("title") or ""), col={"sm":12,"md":6}),
            "author": admin_text_field(label="Author", value=str(source.get("author") or ""), col={"sm":12,"md":6}),
            "publisher": admin_text_field(label="Publisher", value=str(source.get("publisher") or ""), col={"sm":12,"md":6}),
            "publication_year": admin_text_field(label="Publication year", value=str(source.get("publication_year") or ""), col={"sm":12,"md":4}),
            "category": admin_text_field(label="Category", value=str(source.get("category") or ""), col={"sm":12,"md":4}),
            "shelf_location": admin_text_field(label="Shelf location", value=str(source.get("shelf_location") or ""), col={"sm":12,"md":4}),
            "description": admin_text_field(label="Description", value=str(source.get("description") or ""), multiline=True, min_lines=3, max_lines=5, col=12),
            "keywords": admin_text_field(label="Keywords (comma separated)", value=", ".join(source.get("keywords") or []), col={"sm":12,"md":6}),
            "subjects": admin_text_field(label="Subjects (comma separated)", value=", ".join(source.get("subjects") or []), col={"sm":12,"md":6}),
        }
        if creating:
            fields["initial_copy_count"] = admin_text_field(label="Initial physical copies", value="1", col={"sm":12,"md":4})
        cover_picker = ImagePickerControl(page, "Book cover", source.get("cover_url"))

        def close_form() -> None:
            cover_picker.cleanup()
            if cover_picker.picker in page.overlay:
                page.overlay.remove(cover_picker.picker)
            page.close(dialog)

        def save(_event) -> None:
            if save_button.disabled:
                return
            payload = book_payload(fields, creating)
            if payload is None:
                return
            set_button_loading(save_button, True, "Save book", "Saving…")
            page.update()
            result = admin_catalog_service.create_book(payload) if creating else admin_catalog_service.update_book(int(source["id"]), payload)
            if not result.ok:
                set_button_loading(save_button, False, "Save book")
                show_notice(result.error_kind, result.message, "Book was not saved")
                return
            image_warning = None
            if cover_picker.selected_path:
                set_button_loading(save_button, True, "Save book", "Uploading cover…")
                page.update()
                uploaded = admin_catalog_service.upload_book_cover(int(result.data["id"]), str(cover_picker.selected_path))
                if not uploaded.ok:
                    image_warning = uploaded.message
            close_form()
            if image_warning:
                show_notice("validation_error", f"The catalog record was saved, but the cover was not uploaded: {image_warning}", "Cover upload incomplete")
            else:
                show_notice("success", "Catalog record created." if creating else "Catalog record updated.")
            load()

        save_button = ft.FilledButton("Save book", icon=ft.Icons.SAVE_ROUNDED, on_click=save)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add catalog title" if creating else "Edit catalog title"),
            content=ft.Container(
                width=640,
                height=540,
                content=ft.Column(scroll=ft.ScrollMode.AUTO, spacing=18, controls=[
                    form_section("Book identity","Core bibliographic information used in the catalog.",[fields["isbn"],fields["title"],fields["author"],fields["publisher"]]),
                    cover_picker.control,
                    ft.Divider(height=1,color=Colors.BORDER),
                    form_section("Classification and location","Help students find the correct physical shelf.",[fields["publication_year"],fields["category"],fields["shelf_location"]]),
                    *([ft.Divider(height=1,color=Colors.BORDER), form_section("Physical inventory","Create accessioned, available copies with secure QR tokens in the same transaction.",[fields["initial_copy_count"]])] if creating else []),
                    ft.Divider(height=1,color=Colors.BORDER),
                    form_section("Discovery information","Description, subjects, and keywords improve search and recommendations.",[fields["description"],fields["keywords"],fields["subjects"]]),
                ]),
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _e: close_form()),
                save_button,
            ],
        )
        page.open(dialog)

    def rotate_copy_qr(copy: dict) -> None:
        def confirm(_event, dialog) -> None:
            result = admin_catalog_service.rotate_copy_qr(int(copy["id"]))
            page.close(dialog)
            if result.ok:
                qr_dialog(page, "Book copy QR", result.data["qr_image"], str(copy.get("accession_number", "")), replaced=True, download_url=result.data.get("download_url"))
            else:
                show_notice(result.error_kind, result.message)

        confirmation_dialog(
            page,
            "Replace copy QR code?",
            "The previous QR code will stop working immediately.",
            "Replace QR",
            confirm,
        )

    def view_copy_qr(copy: dict) -> None:
        result = admin_catalog_service.get_copy_qr(int(copy["id"]))
        if result.ok:
            qr_dialog(page, "Book copy QR", result.data["qr_image"], str(copy.get("accession_number", "")), download_url=result.data.get("download_url"))
        else:
            show_notice(result.error_kind, result.message)

    def open_copies(book: dict) -> None:
        copy_body = ft.Column(spacing=Spacing.SM)
        copy_notice = ft.Column()
        quantity = admin_text_field(label="Number of copies", value="1", width=170)
        accessions = admin_text_field(label="Accession numbers (optional, comma separated)", expand=True)

        def load_copies(update: bool = True) -> None:
            result = admin_catalog_service.list_copies(int(book["id"]))
            copy_body.controls.clear()
            if not result.ok:
                copy_body.controls.append(Alert(result.error_kind, result.message))
            elif not result.data:
                copy_body.controls.append(EmptyState("No physical copies", "Add the first accessioned copy for this title."))
            else:
                for item in result.data:
                    status = admin_dropdown(
                        value=str(item.get("status", "AVAILABLE")).upper(),
                        width=145,
                        options=[ft.dropdown.Option(value) for value in COPY_STATUSES],
                    )

                    def change_status(_event, copy=item, control=status) -> None:
                        response = admin_catalog_service.update_copy_status(int(copy["id"]), str(control.value))
                        copy_notice.controls = [Alert("success", "Copy status updated.")] if response.ok else [Alert(response.error_kind, response.message)]
                        if not response.ok:
                            control.value = str(copy.get("status", "AVAILABLE")).upper()
                        else:
                            copy["status"] = control.value
                        page.update()

                    status.on_change = change_status
                    copy_body.controls.append(
                        ft.Container(
                            padding=ft.padding.symmetric(vertical=8),
                            border=ft.border.only(bottom=ft.BorderSide(1, Colors.BORDER)),
                            content=ft.Row(
                                controls=[
                                    ft.Text(str(item.get("accession_number", "")), width=210, weight=ft.FontWeight.W_600),
                                    status,
                                    ft.IconButton(ft.Icons.QR_CODE_2_ROUNDED, tooltip="View QR", on_click=lambda _e, copy=item: view_copy_qr(copy)),
                                    ft.IconButton(ft.Icons.REFRESH_ROUNDED, tooltip="Replace QR", on_click=lambda _e, copy=item: rotate_copy_qr(copy)),
                                ]
                            ),
                        )
                    )
            if update:
                page.update()

        def add(_event) -> None:
            raw = str(quantity.value or "").strip()
            numbers = [x.strip() for x in str(accessions.value or "").split(",") if x.strip()]
            if not raw.isdigit() or not 1 <= int(raw) <= 100:
                copy_notice.controls = [Alert("validation_error", "Quantity must be between 1 and 100.")]
                page.update()
                return
            if numbers and len(numbers) != int(raw):
                copy_notice.controls = [Alert("validation_error", "The number of accession numbers must match the quantity.")]
                page.update()
                return
            result = admin_catalog_service.add_copies(int(book["id"]), int(raw), numbers or None)
            copy_notice.controls = [Alert("success", f"Added {raw} physical copy/copies.")] if result.ok else [Alert(result.error_kind, result.message)]
            if result.ok:
                accessions.value = ""
                load_copies(update=False)
                load()
            page.update()

        def download_sheet(_event) -> None:
            result = admin_catalog_service.create_copy_qr_sheet(int(book["id"]))
            if result.ok:
                copy_notice.controls = [Alert("success", f"Printable sheet created for {result.data['copy_count']} copy QR code(s).")]
                page.update()
                page.launch_url(result.data["download_url"])
            else:
                copy_notice.controls = [Alert(result.error_kind, result.message)]
                page.update()

        load_copies(update=False)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Physical copies — {book.get('title', '')}"),
            content=ft.Container(
                width=690,
                height=520,
                content=ft.Column(
                    controls=[
                        ft.Text("Each physical item has its own accession number, status, and secure QR code.", color=Colors.TEXT_SECONDARY),
                        ft.Row(controls=[quantity, accessions, ft.FilledButton("Add", icon=ft.Icons.ADD_ROUNDED, on_click=add)]),
                        copy_notice,
                        ft.Divider(),
                        ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, controls=[copy_body]),
                    ]
                ),
            ),
            actions=[ft.OutlinedButton("Download QR sheet", icon=ft.Icons.PICTURE_AS_PDF_OUTLINED, on_click=download_sheet), ft.FilledButton("Done", on_click=lambda _e: page.close(dialog))],
        )
        page.open(dialog)

    def archive(book: dict) -> None:
        def confirm(_event, dialog) -> None:
            result = admin_catalog_service.archive_book(int(book["id"]))
            page.close(dialog)
            show_notice("success", "Book archived. Available copies were archived too.") if result.ok else show_notice(result.error_kind, result.message)
            if result.ok:
                load()

        confirmation_dialog(
            page,
            "Archive this title?",
            "It will disappear from the public catalog. Active borrowed copies are not changed.",
            "Archive book",
            confirm,
        )

    def restore(book: dict) -> None:
        result = admin_catalog_service.update_book(int(book["id"]), {"is_archived": False})
        show_notice("success", "Book restored to the public catalog.") if result.ok else show_notice(result.error_kind, result.message)
        if result.ok:load()

    def actions(book: dict) -> ft.PopupMenuButton:
        items = [
            ft.PopupMenuItem(text="Edit catalog record", icon=ft.Icons.EDIT_OUTLINED, on_click=lambda _e: open_book_form(book)),
            ft.PopupMenuItem(text="Manage physical copies", icon=ft.Icons.COPY_ALL_ROUNDED, on_click=lambda _e: open_copies(book)),
        ]
        if not book.get("is_archived"):
            items.append(ft.PopupMenuItem(text="Archive title", icon=ft.Icons.ARCHIVE_OUTLINED, on_click=lambda _e: archive(book)))
        else:
            items.append(ft.PopupMenuItem(text="Restore title", icon=ft.Icons.UNARCHIVE_OUTLINED, on_click=lambda _e: restore(book)))
        return ft.PopupMenuButton(icon=ft.Icons.MORE_HORIZ_ROUNDED, tooltip="Book actions", items=items)

    def load(_event=None, show_loading: bool = True) -> None:
        if show_loading:
            body.controls = [InlineLoading("Loading catalog titles…")]
            page.update()
        result = admin_catalog_service.list_books(
            str(search.value or "").strip() or None,
            str(category_filter.value or "").strip() or None,
            str(author_filter.value or "").strip() or None,
            str(shelf_filter.value or "").strip() or None,
            bool(available_filter.value),
            state["offset"],
            PAGE_SIZE,
            bool(include_archived.value),
        )
        body.controls.clear()
        if not result.ok:
            body.controls.append(Alert(result.error_kind, result.message))
            page.update()
            return
        payload = result.data if isinstance(result.data, dict) else {"items": result.data, "total": len(result.data)}
        rows = payload.get("items", [])
        state["total"] = int(payload.get("total", len(rows)))
        if not rows:
            body.controls.append(EmptyState("No catalog titles found", "Change the search or add a new book.", ft.Icons.MENU_BOOK_OUTLINED))
        else:
            table = ft.DataTable(
                heading_row_color="#F8FAFC",
                column_spacing=table_width(24),
                horizontal_margin=20,
                columns=[ft.DataColumn(ft.Text(x, weight=ft.FontWeight.W_600)) for x in ["Title", "Author", "Category", "Copies", "Shelf", "Status", ""]],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Container(width=table_width(260), content=ft.Row(controls=[ft.Container(width=34,height=46,border_radius=4,clip_behavior=ft.ClipBehavior.ANTI_ALIAS,bgcolor=Colors.PRIMARY_MUTED,alignment=ft.alignment.center,content=ft.Image(src=book.get("cover_url"),fit=ft.ImageFit.COVER) if book.get("cover_url") else ft.Icon(ft.Icons.MENU_BOOK_OUTLINED,size=17,color=Colors.PRIMARY)),ft.Column(expand=True, tight=True, spacing=1, controls=[ft.Text(str(book.get("title", "")), weight=ft.FontWeight.W_600, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS), ft.Text(str(book.get("isbn", "")), size=11, color=Colors.TEXT_SECONDARY)])]))),
                            ft.DataCell(ft.Text(str(book.get("author", "")), width=table_width(160), max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)),
                            ft.DataCell(ft.Text(str(book.get("category", "—")), width=table_width(125), max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)),
                            ft.DataCell(ft.Container(width=table_width(80), content=ft.Text(f"{book.get('available_copies', 0)} / {book.get('total_copies', 0)}"))),
                            ft.DataCell(ft.Text(str(book.get("shelf_location", "—")), width=table_width(115), max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)),
                            ft.DataCell(ft.Container(width=table_width(95), alignment=ft.alignment.center_left, content=status_badge("archived" if book.get("is_archived") else "active"))),
                            ft.DataCell(ft.Container(width=table_width(44), alignment=ft.alignment.center, content=actions(book))),
                        ]
                    )
                    for book in rows
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

    def import_csv(_event=None) -> None:
        csv_picker.pick_files(dialog_title="Import catalog CSV", allowed_extensions=["csv"], allow_multiple=False)

    def csv_selected(event) -> None:
        if not event.files:
            return
        result = admin_catalog_service.import_books(event.files[0].path)
        show_notice("success" if result.ok else result.error_kind, "Catalog imported successfully." if result.ok else result.message, "Import complete" if result.ok else "Import failed")
        if result.ok:
            load()

    csv_picker.on_result = csv_selected

    search.on_submit = new_search
    include_archived.on_change = new_search
    available_filter.on_change = new_search
    toolbar = ft.Row(
        spacing=Spacing.SM,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(expand=True, content=search),
            ft.Container(height=50, alignment=ft.alignment.center_left, content=include_archived),
            category_filter,
            author_filter,
            shelf_filter,
            available_filter,
            ft.OutlinedButton("Refresh", icon=ft.Icons.REFRESH_ROUNDED, on_click=new_search),
            ft.OutlinedButton("Import CSV", icon=ft.Icons.UPLOAD_FILE_ROUNDED, on_click=import_csv),
            ft.FilledButton("Add book", icon=ft.Icons.ADD_ROUNDED, on_click=lambda _e: open_book_form()),
        ],
    )
    load(show_loading=False)
    content = ft.Column(tight=True, spacing=Spacing.LG, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, controls=[section_card(toolbar, padding=Spacing.MD), notice, body, pager])
    return AdminView(page, Routes.ADMIN_BOOKS, "Books", content, subtitle="Manage catalog titles and separately tracked physical copies")
