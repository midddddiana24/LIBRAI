"""
LIBRAI – Kiosk Home Page
========================
Primary self-service screen. Clean, spacious, touch-optimised.
School-library aesthetic: calm navy, warm gold accents, generous whitespace.
"""

from __future__ import annotations
import flet as ft

from components.app_header import AppHeader
from components.brand_logo import BrandLogo
from components.search_bar import SearchBar
from core.config    import settings
from core.constants import Routes
from core.theme     import Colors, Radius, Spacing, Shadow


# ─────────────────────────────────────────────────────────────
#  HERO BANNER
# ─────────────────────────────────────────────────────────────
def _hero(page: ft.Page) -> ft.Container:
    compact = (getattr(page, "width", None) or 1366) < 820
    def search(q: str) -> None:
        if q.strip():
            page.client_storage.set("librai_pending_search", q.strip())
        page.go(Routes.SEARCH)

    return ft.Container(
        border_radius=Radius.LG,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        shadow=Shadow.sm(),
        padding=ft.padding.symmetric(horizontal=Spacing.LG if compact else Spacing.XL, vertical=Spacing.LG),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.LG,
            controls=[
                BrandLogo(170 if compact else 210, 108 if compact else 128),
                # Eyebrow label
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=6),
                    border_radius=Radius.PILL,
                    bgcolor=Colors.PRIMARY_MUTED,
                    border=ft.border.all(1, Colors.BORDER),
                    content=ft.Row(
                        tight=True, spacing=7,
                        controls=[
                            ft.Icon(ft.Icons.LOCAL_LIBRARY_ROUNDED, size=13, color=Colors.PRIMARY),
                            ft.Text(
                                "LIBRARY SELF-SERVICE KIOSK",
                                size=10,
                                weight=ft.FontWeight.W_700,
                                color=Colors.PRIMARY,
                            ),
                        ],
                    ),
                ),
                # Headline
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.Text(
                            settings.school_name,
                            size=13,
                            weight=ft.FontWeight.W_500,
                            color=Colors.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "How can we help you today?",
                            size=27 if compact else 32,
                            weight=ft.FontWeight.W_800,
                            color=Colors.TEXT_PRIMARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "Borrow, return, discover and manage your library account.",
                            size=14,
                            color=Colors.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
                # Search bar (white surface on dark bg)
                ft.Container(
                    width=500 if compact else 560,
                    content=SearchBar(
                        on_submit=search,
                        compact=True,
                    ),
                ),
            ],
        ),
    )


# ─────────────────────────────────────────────────────────────
#  PRIMARY ACTION TILE
# ─────────────────────────────────────────────────────────────
def _action_tile(
    page: ft.Page,
    icon: str,
    label: str,
    description: str,
    route: str,
    accent: str,
    before_navigate=None,
) -> ft.Container:
    def hover(event: ft.ControlEvent) -> None:
        tile = event.control
        active = str(event.data).lower() == "true"
        tile.bgcolor = Colors.SURFACE if not active else Colors.SURFACE_ALT
        tile.border = ft.border.all(1.5 if active else 1, accent if active else Colors.BORDER)
        tile.shadow = Shadow.sm() if active else None
        tile.scale = 1.012 if active else 1
        tile.update()

    return ft.Container(
        height=136,
        bgcolor=Colors.SURFACE,
        border_radius=Radius.LG,
        border=ft.border.all(1, Colors.BORDER),
        padding=Spacing.MD,
        ink=True,
        animate=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(160, ft.AnimationCurve.EASE_OUT),
        on_hover=hover,
        on_click=lambda _e: (before_navigate() if before_navigate else None, page.go(route)),
        content=ft.Column(
            spacing=Spacing.SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                # Accent icon tile
                ft.Container(
                    width=42, height=42,
                    border_radius=Radius.SM,
                    bgcolor=ft.Colors.with_opacity(0.11, accent),
                    alignment=ft.alignment.center,
                    content=ft.Icon(icon, size=23, color=accent),
                ),
                ft.Column(
                    tight=True,
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(label, size=14, weight=ft.FontWeight.W_700,
                                color=Colors.TEXT_PRIMARY, text_align=ft.TextAlign.CENTER),
                        ft.Text(description, size=10, color=Colors.TEXT_SECONDARY,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, text_align=ft.TextAlign.CENTER),
                    ],
                ),
            ],
        ),
    )


# ─────────────────────────────────────────────────────────────
#  SHORTCUT CHIP
# ─────────────────────────────────────────────────────────────
def _chip(page: ft.Page, icon: str, label: str, route: str) -> ft.Container:
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=10),
        border_radius=Radius.PILL,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        ink=False,
        on_click=lambda _e: page.go(route),
        content=ft.Row(
            tight=True, spacing=7,
            controls=[
                ft.Icon(icon, size=16, color=Colors.PRIMARY),
                ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                        color=Colors.TEXT_PRIMARY),
            ],
        ),
    )


# ─────────────────────────────────────────────────────────────
#  BUILD  (entry point called by router)
# ─────────────────────────────────────────────────────────────
def build(page: ft.Page) -> ft.View:
    actions = ft.ResponsiveRow(
        columns=12,
        spacing=Spacing.MD,
        run_spacing=Spacing.MD,
        controls=[
            ft.Container(
                col={"xs": 6, "md": 4},
                content=_action_tile(
                    page,
                    ft.Icons.QR_CODE_SCANNER_ROUNDED,
                    "Borrow a Book",
                    "Scan your library card QR, then the book copy QR.",
                    Routes.BORROW_SCAN_USER,
                    Colors.PRIMARY,
                ),
            ),
            ft.Container(
                col={"xs": 6, "md": 4},
                content=_action_tile(
                    page,
                    ft.Icons.ASSIGNMENT_RETURN_ROUNDED,
                    "Return a Book",
                    "Scan the QR attached to the physical book copy.",
                    Routes.RETURN_SCAN_BOOK,
                    Colors.SUCCESS,
                ),
            ),
            ft.Container(
                col={"xs": 6, "md": 4},
                content=_action_tile(
                    page,
                    ft.Icons.SEARCH_ROUNDED,
                    "Search the Catalog",
                    "Find books by title, author, ISBN, or subject.",
                    Routes.SEARCH,
                    Colors.WARNING,
                ),
            ),
            ft.Container(
                col={"xs": 6, "md": 4},
                content=_action_tile(
                    page,
                    ft.Icons.AUTO_AWESOME_ROUNDED,
                    "Ask LIBRAI",
                    "Describe what you need — AI finds the right book.",
                    Routes.AI_ASSISTANT,
                    Colors.BRAND_GREEN,
                ),
            ),
            ft.Container(col={"xs": 6, "md": 4}, content=_action_tile(page, ft.Icons.PERSON_OUTLINE_ROUNDED, "My Account", "Loans, due dates and history", Routes.ACCOUNT, Colors.PRIMARY)),
            ft.Container(col={"xs": 6, "md": 4}, content=_action_tile(page, ft.Icons.RECOMMEND_OUTLINED, "Recommendations", "Books selected for you", Routes.RECOMMENDATIONS, "#7C3AED")),
            ft.Container(col={"xs": 6, "md": 4}, content=_action_tile(page, ft.Icons.NEW_RELEASES_OUTLINED, "New Books", "Recently added titles", Routes.NEW_BOOKS, Colors.SUCCESS)),
            ft.Container(col={"xs": 6, "md": 4}, content=_action_tile(page, ft.Icons.TRENDING_UP_ROUNDED, "Popular Books", "Most borrowed titles", Routes.POPULAR_BOOKS, Colors.WARNING)),
            ft.Container(col={"xs": 6, "md": 4}, content=_action_tile(page, ft.Icons.BOOKMARK_BORDER_ROUNDED, "Reservations", "View your reservation queue", Routes.RESERVATIONS, "#B45309")),
        ],
    )

    shortcuts = ft.Row(
        wrap=True,
        spacing=Spacing.SM,
        run_spacing=Spacing.SM,
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            _chip(page, ft.Icons.RECOMMEND_OUTLINED,    "Recommended",  Routes.RECOMMENDATIONS),
            _chip(page, ft.Icons.NEW_RELEASES_OUTLINED, "New Arrivals", Routes.NEW_BOOKS),
            _chip(page, ft.Icons.TRENDING_UP_ROUNDED,   "Popular Books",Routes.POPULAR_BOOKS),
            _chip(page, ft.Icons.PERSON_OUTLINE_ROUNDED,"My Account",   Routes.ACCOUNT),
            _chip(page, ft.Icons.BOOKMARK_BORDER_ROUNDED,"Reservations",Routes.RESERVATIONS),
        ],
    )

    footer = ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, size=13, color=Colors.TEXT_DISABLED),
            ft.Container(width=5),
            ft.Text(
                "Need assistance? Please ask a library staff member.",
                size=11, color=Colors.TEXT_DISABLED,
            ),
        ],
    )

    body = ft.Container(
        expand=True,
        bgcolor=Colors.BACKGROUND,
        alignment=ft.alignment.top_center,
        padding=ft.padding.symmetric(horizontal=Spacing.MD if (getattr(page, "width", None) or 1366) < 820 else Spacing.XL, vertical=Spacing.LG if (getattr(page, "width", None) or 1366) < 820 else Spacing.XL),
        content=ft.Container(
            width=1000,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=Spacing.LG,
                controls=[
                    _hero(page),
                    # Section heading
                    ft.Row(
                        controls=[
                            ft.Container(width=4, height=20, bgcolor=Colors.BRAND_GREEN,
                                         border_radius=Radius.PILL),
                            ft.Container(width=8),
                            ft.Text("What would you like to do?", size=15,
                                    weight=ft.FontWeight.W_700, color=Colors.TEXT_PRIMARY),
                        ],
                    ),
                    actions,
                    ft.Container(height=Spacing.SM),
                    footer,
                ],
            ),
        ),
    )

    return ft.View(
        route=Routes.HOME,
        bgcolor=Colors.BACKGROUND,
        padding=0,
        scroll=ft.ScrollMode.AUTO,
        controls=[AppHeader(page, title="Self-Service", show_home=False), body],
    )
