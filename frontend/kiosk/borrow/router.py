from __future__ import annotations

import flet as ft

from components.alert import Alert
from components.page_shell import KioskView
from components.qr_scanner_view import QRScannerView
from core.constants import Routes
from core.state import get_state
from core.theme import Colors, Radius, Spacing, touch_button_style
from services.api_client import ApiResult
from services.borrowing_service import borrowing_service
from services.qr_service import qr_service
from utils.formatting import format_date


def _value(value, fallback: str = "-") -> str:
    return str(value) if value not in (None, "") else fallback


def _meta_row(label: str, value) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(label, color=Colors.TEXT_SECONDARY),
            ft.Text(_value(value), weight=ft.FontWeight.W_600),
        ],
    )


def _steps(active: int) -> ft.Row:
    labels = ["User QR", "Verify user", "Book QR", "Confirm", "Complete"]
    return ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        wrap=True,
        controls=[
            ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                border_radius=99,
                bgcolor=Colors.PRIMARY if i <= active else "#E5E7EB",
                content=ft.Text(
                    f"{i + 1}. {label}",
                    color=Colors.ON_PRIMARY if i <= active else Colors.TEXT_SECONDARY,
                    size=12,
                ),
            )
            for i, label in enumerate(labels)
        ],
    )


def _scan_user(page):
    state = get_state(page)
    status = ft.Column()

    def scan(token):
        result = qr_service.verify_user(token)
        if result.ok:
            state.kiosk_user = result.data
            page.go(Routes.BORROW_USER_VERIFIED)
        else:
            status.controls = [Alert(result.error_kind, result.message)]
            page.update()
        return result

    return KioskView(
        page,
        Routes.BORROW_SCAN_USER,
        "Borrow Book",
        [
            _steps(0),
            status,
            QRScannerView(
                page,
                "Scan Your Library QR",
                "Your QR is verified securely by the library server.",
                scan,
                "Library user QR token",
            ),
        ],
    )


def _verified(page):
    state = get_state(page)
    if not state.kiosk_user:
        return _scan_user(page)

    user = state.kiosk_user
    rows = [
        ("Name", user.get("name")),
        ("Student ID", user.get("student_id")),
        ("Course", user.get("course")),
        ("Account status", _value(user.get("account_status"), "unknown").title()),
        (
            "Current borrowed",
            f"{user.get('current_borrowed_count', 0)} of {_value(user.get('borrowing_limit'))}",
        ),
        ("Overdue status", "Has overdue items" if user.get("has_overdue") else "Clear"),
    ]
    can_borrow = bool(user.get("can_borrow", True))
    photo = ft.Container(
        width=112,
        height=132,
        border_radius=Radius.MD,
        bgcolor=Colors.PRIMARY_MUTED,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        alignment=ft.alignment.center,
        content=ft.Image(src=user.get("photo_url"), fit=ft.ImageFit.COVER)
        if user.get("photo_url")
        else ft.Icon(ft.Icons.ACCOUNT_CIRCLE_ROUNDED, size=70, color=Colors.PRIMARY),
    )
    restriction = []
    if not can_borrow:
        restriction.append(
            Alert(
                "validation_error",
                "This account cannot borrow right now. Check the account status, borrowing limit, and overdue items.",
                title="Borrowing restricted",
            )
        )

    details = ft.Column(
        # Do not use expand inside a wrapping Row. On kiosk window sizes
        # Flet can allocate the expanded child the full remaining height,
        # hiding the verification details and Continue button below it.
        width=520,
        controls=[
            ft.Text(
                "User Verified",
                size=26,
                weight=ft.FontWeight.BOLD,
                color=Colors.SUCCESS,
            ),
            *[_meta_row(label, value) for label, value in rows],
        ],
    )
    card = ft.Container(
        width=720,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.LG,
        padding=Spacing.XL,
        content=ft.Column(
            spacing=Spacing.LG,
            controls=[
                ft.Row(
                    wrap=True,
                    spacing=Spacing.LG,
                    run_spacing=Spacing.LG,
                    controls=[photo, details],
                ),
                *restriction,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.OutlinedButton(
                            "Cancel",
                            on_click=lambda e: (state.clear_kiosk(), page.go(Routes.HOME)),
                        ),
                        ft.FilledButton(
                            "Continue",
                            icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                            style=touch_button_style(),
                            disabled=not can_borrow,
                            on_click=lambda e: page.go(Routes.BORROW_SCAN_BOOK),
                        ),
                    ],
                ),
            ],
        ),
    )
    return KioskView(
        page,
        Routes.BORROW_USER_VERIFIED,
        "Borrow Book",
        [_steps(1), ft.Container(alignment=ft.alignment.center, content=card)],
        user.get("name"),
    )


def _scan_book(page):
    state = get_state(page)
    if not state.kiosk_user:
        return _scan_user(page)

    status = ft.Column()

    def scan(token):
        result = qr_service.verify_book(token)
        if result.ok and not bool(result.data.get("can_borrow", result.data.get("available", False))):
            result = ApiResult.failure(
                "validation_error",
                "This physical copy is not available for borrowing.",
                409,
            )
        if result.ok:
            state.scanned_book = result.data
            page.go(Routes.BORROW_CONFIRM)
        else:
            status.controls = [Alert(result.error_kind, result.message)]
            page.update()
        return result

    return KioskView(
        page,
        Routes.BORROW_SCAN_BOOK,
        "Borrow Book",
        [
            _steps(2),
            status,
            QRScannerView(
                page,
                "Scan Book QR",
                "Scan the secure QR attached to the physical book copy.",
                scan,
                "Book-copy QR token",
            ),
        ],
        state.kiosk_user.get("name"),
    )


def _confirm(page):
    state = get_state(page)
    if not state.kiosk_user:
        return _scan_user(page)
    if not state.scanned_book:
        return _scan_book(page)

    book = state.scanned_book
    status = ft.Column()

    def submit(_e):
        if confirm_button.disabled:
            return
        confirm_button.disabled = True
        confirm_button.text = "Processing..."
        status.controls = [
            ft.Row(
                controls=[
                    ft.ProgressRing(width=22, height=22, stroke_width=3),
                    ft.Text("Checking account, policy, availability, and processing transaction..."),
                ]
            )
        ]
        page.update()

        result = borrowing_service.create(
            state.kiosk_user["id"],
            book["id"],
            state.kiosk_user.get("verification_token"),
            book.get("verification_token"),
        )
        if result.ok:
            state.last_transaction = result.data
            page.go(Routes.BORROW_SUCCESS)
        else:
            confirm_button.disabled = False
            confirm_button.text = "Confirm Borrow"
            status.controls = [Alert(result.error_kind, result.message)]
            page.update()

    can_borrow = bool(book.get("can_borrow", book.get("available", False)))
    confirm_button = ft.FilledButton(
        "Confirm Borrow",
        icon=ft.Icons.CHECK_ROUNDED,
        style=touch_button_style(),
        disabled=not can_borrow,
        on_click=submit,
    )
    cover = ft.Container(
        width=170,
        height=230,
        bgcolor="#E8EDF7",
        border_radius=Radius.MD,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        alignment=ft.alignment.center,
        content=ft.Image(src=book.get("cover_url"), fit=ft.ImageFit.COVER)
        if book.get("cover_url")
        else ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, size=64, color=Colors.PRIMARY),
    )
    availability_text = "Available" if book.get("available") else "Unavailable"
    details = [
        ft.Text(_value(book.get("title"), "Untitled book"), size=25, weight=ft.FontWeight.BOLD),
        ft.Text(_value(book.get("author"), "Unknown author"), color=Colors.TEXT_SECONDARY),
        _meta_row("Category", book.get("category")),
        _meta_row("ISBN", book.get("isbn")),
        _meta_row("Publisher", book.get("publisher")),
        _meta_row("Year", book.get("publication_year")),
        _meta_row("Copy ID", book.get("copy_id") or book.get("accession_number")),
        _meta_row("Shelf", book.get("shelf_location")),
        ft.Text(
            availability_text,
            weight=ft.FontWeight.W_700,
            color=Colors.SUCCESS if book.get("available") else Colors.ERROR,
        ),
    ]
    if book.get("description"):
        details.append(ft.Text(book.get("description"), color=Colors.TEXT_SECONDARY, max_lines=3))

    card = ft.Container(
        width=760,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.LG,
        padding=Spacing.XL,
        content=ft.Row(
            wrap=True,
            spacing=Spacing.XL,
            controls=[
                cover,
                ft.Column(
                    # Keep a bounded width inside the wrapping Row. An
                    # expanded child can consume the row's available height
                    # on kiosk sizes and make the book details appear blank.
                    width=520,
                    spacing=Spacing.SM,
                    controls=[
                        *details,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.END,
                            controls=[
                                ft.OutlinedButton(
                                    "Cancel",
                                    on_click=lambda e: (state.clear_kiosk(), page.go(Routes.HOME)),
                                ),
                                confirm_button,
                            ],
                        ),
                        status,
                    ],
                ),
            ],
        ),
    )
    return KioskView(
        page,
        Routes.BORROW_CONFIRM,
        "Borrow Book",
        [_steps(3), ft.Container(alignment=ft.alignment.center, content=card)],
        state.kiosk_user.get("name"),
    )


def _success(page):
    state = get_state(page)
    transaction = state.last_transaction or {}

    def another(_e):
        state.scanned_book = None
        state.last_transaction = None
        page.go(Routes.BORROW_SCAN_BOOK)

    def finish(_e):
        state.clear_kiosk()
        page.go(Routes.HOME)

    card = ft.Container(
        width=680,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.LG,
        padding=Spacing.XL,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=84, color=Colors.SUCCESS),
                ft.Text("Borrowing Successful", size=30, weight=ft.FontWeight.BOLD),
                ft.Text(transaction.get("book_title", "Book"), size=19),
                ft.Text(f"Borrowed: {format_date(transaction.get('borrowed_at'))}"),
                ft.Text(
                    f"Due date: {format_date(transaction.get('due_at'))}",
                    weight=ft.FontWeight.BOLD,
                    color=Colors.WARNING,
                ),
                ft.Text(
                    f"Transaction ID: {transaction.get('transaction_id', transaction.get('id', '-'))}",
                    size=12,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Row(
                    wrap=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.OutlinedButton("Borrow Another Book", on_click=another),
                        ft.FilledButton("Finish", on_click=finish),
                    ],
                ),
            ],
        ),
    )
    return KioskView(
        page,
        Routes.BORROW_SUCCESS,
        "Borrow Book",
        [_steps(4), ft.Container(alignment=ft.alignment.center, content=card)],
    )


def build_view(route, page):
    routes = {
        Routes.BORROW_SCAN_USER: _scan_user,
        Routes.BORROW_USER_VERIFIED: _verified,
        Routes.BORROW_SCAN_BOOK: _scan_book,
        Routes.BORROW_CONFIRM: _confirm,
        Routes.BORROW_SUCCESS: _success,
    }
    return routes.get(route, _scan_user)(page)
