"""
LIBRAI - Central router.

Maps route paths (see core/constants.Routes) to page-building
functions. app.py listens to `page.on_route_change` and calls
`build_view(route, page)` here to get the ft.View to display.

Keeping this centralized means individual page modules stay simple
(just export a `build(page) -> ft.View` function) and never need to
know about each other's routes directly, except via Routes.* constants.
"""

from __future__ import annotations

import flet as ft

from core.constants import Routes
from kiosk import home_page

# NOTE: Additional page modules are imported lazily inside build_view
# as they are implemented (Phase 2+), to avoid import errors for
# not-yet-created modules breaking the whole app during incremental
# development.


def build_view(route: str, page: ft.Page) -> ft.View:
    """Resolve a route string to a fully-built ft.View.

    Falls back to the kiosk home page for unknown routes so the kiosk
    never shows a blank/broken screen to an end user.
    """

    if route == Routes.HOME or route == "":
        return home_page.build(page)

    if route == Routes.SEARCH:
        try:
            from kiosk import search_page

            return search_page.build(page)
        except ImportError:
            return _not_yet_implemented(page, "Search")

    if route.startswith(Routes.BOOK_DETAILS):
        try:
            from kiosk import book_details_page

            return book_details_page.build(page)
        except ImportError as exc:
            return _feature_load_error(page, "Book Details", exc)

    if route == Routes.AI_ASSISTANT:
        try:
            from kiosk import ai_assistant_page

            return ai_assistant_page.build(page)
        except ImportError:
            return _not_yet_implemented(page, "LIBRAI Assistant")

    if route == Routes.RECOMMENDATIONS:
        try:
            from kiosk import recommendations_page

            return recommendations_page.build(page)
        except ImportError:
            return _not_yet_implemented(page, "Recommendations")

    if route == Routes.POPULAR_BOOKS:
        try:
            from kiosk import popular_books_page

            return popular_books_page.build(page)
        except ImportError:
            return _not_yet_implemented(page, "Popular Books")

    if route == Routes.NEW_BOOKS:
        try:
            from kiosk import new_books_page

            return new_books_page.build(page)
        except ImportError:
            return _not_yet_implemented(page, "New Books")

    if route == Routes.ACCOUNT:
        try:
            from kiosk import account_page

            return account_page.build(page)
        except ImportError:
            return _not_yet_implemented(page, "My Account")

    if route == Routes.RESERVATIONS:
        try:
            from kiosk import reservations_page

            return reservations_page.build(page)
        except ImportError:
            return _not_yet_implemented(page, "Reservations")

    if route.startswith("/borrow"):
        try:
            from kiosk.borrow import router as borrow_router

            return borrow_router.build_view(route, page)
        except ImportError as exc:
            return _feature_load_error(page, "Borrow Book", exc)

    if route.startswith("/return"):
        try:
            from kiosk.return_book import router as return_router

            return return_router.build_view(route, page)
        except ImportError as exc:
            return _feature_load_error(page, "Return Book", exc)

    if route.startswith("/admin"):
        try:
            from admin import router as admin_router

            return admin_router.build_view(route, page)
        except ImportError:
            return _not_yet_implemented(page, "Admin Panel")

    # Unknown route -> kiosk home (never leave the kiosk on a blank page)
    return home_page.build(page)


def _not_yet_implemented(page: ft.Page, feature_name: str) -> ft.View:
    """Placeholder view shown while a feature is still being built in
    a later phase, instead of crashing the whole kiosk app."""
    from core.theme import Colors, Spacing

    return ft.View(
        route=page.route,
        bgcolor=Colors.BACKGROUND,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=Spacing.MD,
                    controls=[
                        ft.Icon(ft.Icons.CONSTRUCTION_ROUNDED, size=64, color=Colors.TEXT_SECONDARY),
                        ft.Text(f"{feature_name} is coming soon", size=20, weight=ft.FontWeight.BOLD),
                        ft.Text("This part of LIBRAI is still being built.", color=Colors.TEXT_SECONDARY),
                        ft.FilledButton(
                            "Back to Home",
                            icon=ft.Icons.HOME_ROUNDED,
                            on_click=lambda e: page.go(Routes.HOME),
                        ),
                    ],
                ),
            )
        ],
    )


def _feature_load_error(page: ft.Page, feature_name: str, error: ImportError) -> ft.View:
    """Show an actionable error for a completed feature that failed to load."""
    from core.theme import Colors, Radius, Spacing

    return ft.View(
        route=page.route,
        bgcolor=Colors.BACKGROUND,
        controls=[
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Container(
                    width=560,
                    bgcolor=Colors.SURFACE,
                    border=ft.border.all(1, Colors.BORDER),
                    border_radius=Radius.LG,
                    padding=Spacing.XL,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=Spacing.MD,
                        controls=[
                            ft.Icon(ft.Icons.ERROR_OUTLINE_ROUNDED, size=52, color=Colors.ERROR),
                            ft.Text(f"{feature_name} could not load", size=22, weight=ft.FontWeight.W_700),
                            ft.Text("Restart the frontend after updating the project. If this continues, give the message below to the developer.", color=Colors.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                            ft.Container(bgcolor=Colors.ERROR_BG, border_radius=Radius.SM, padding=Spacing.MD, content=ft.Text(str(error), size=12, color=Colors.ERROR)),
                            ft.FilledButton("Back to Home", icon=ft.Icons.HOME_ROUNDED, on_click=lambda _e: page.go(Routes.HOME)),
                        ],
                    ),
                ),
            )
        ],
    )
