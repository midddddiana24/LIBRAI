"""
LIBRAI – Admin Sidebar & Workspace Shell
=========================================
Refined two-panel admin layout:
  Left  → 240 px dark navy sidebar with grouped navigation + gold active bar
  Right → scrollable content area with sticky page header

Design intent:
  • Sidebar uses the darkest brand navy so the content area reads as white/light
  • Active nav item: left gold accent bar + lighter surface + full-weight label
  • Group labels use all-caps tracking for scannable visual hierarchy
  • Breadcrumb-style page header with action buttons on the right
  • Server health pill subtly visible top-right of content area
"""

from __future__ import annotations
import time
import flet as ft

from components.brand_logo import BrandLogo
from core.config    import settings
from core.constants import APP_NAME, Routes
from core.state     import get_state
from core.theme     import Colors, Radius, Spacing, Shadow
from services.auth_service  import auth_service
from services.api_client    import api_client


# ─────────────────────────────────────────────────────────────
#  NAV STRUCTURE
# ─────────────────────────────────────────────────────────────
GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("OVERVIEW", [
        (Routes.ADMIN_DASHBOARD,    ft.Icons.SPACE_DASHBOARD_OUTLINED,      "Dashboard"),
    ]),
    ("OPERATIONS", [
        (Routes.ADMIN_BORROWINGS,   ft.Icons.OUTPUT_ROUNDED,                "Borrowings"),
        (Routes.ADMIN_RETURNS,      ft.Icons.KEYBOARD_RETURN_ROUNDED,       "Returns"),
        (Routes.ADMIN_RESERVATIONS, ft.Icons.BOOKMARK_BORDER_ROUNDED,       "Reservations"),
        (Routes.ADMIN_FINES,         ft.Icons.PAYMENTS_OUTLINED,             "Fines"),
    ]),
    ("CATALOG & USERS", [
        (Routes.ADMIN_BOOKS,        ft.Icons.MENU_BOOK_OUTLINED,            "Books"),
        (Routes.ADMIN_USERS,        ft.Icons.GROUP_OUTLINED,                "Library Users"),
    ]),
    ("SYSTEM", [
        (Routes.ADMIN_REPORTS,      ft.Icons.INSERT_CHART_OUTLINED_ROUNDED, "Reports"),
        (Routes.ADMIN_AUDIT_LOGS,   ft.Icons.HISTORY_ROUNDED,               "Audit Logs"),
        (Routes.ADMIN_SETTINGS,     ft.Icons.SETTINGS_OUTLINED,             "Settings"),
        (Routes.ADMIN_EMAIL_DELIVERIES, ft.Icons.MARK_EMAIL_UNREAD_OUTLINED, "Email Deliveries"),
    ]),
]

_ALL_NAV = [(r, i, l) for _g, items in GROUPS for (r, i, l) in items]


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────
def _logout(page: ft.Page) -> None:
    state = get_state(page)
    auth_service.logout()
    state.admin_user = None
    state.admin_token = None
    page.client_storage.remove("librai_admin_user")
    page.client_storage.remove("librai_admin_token")
    page.go(Routes.ADMIN_LOGIN)


# ─────────────────────────────────────────────────────────────
#  COMPACT MENU (popup, used when window < 1050 px)
# ─────────────────────────────────────────────────────────────
def AdminMenu(page: ft.Page, active_route: str) -> ft.PopupMenuButton:
    items: list[ft.PopupMenuItem] = []
    for route, icon, label in _ALL_NAV:
        items.append(ft.PopupMenuItem(
            text=label,
            icon=ft.Icons.CHECK_ROUNDED if route == active_route else icon,
            on_click=lambda _e, r=route: page.go(r),
        ))
    items += [
        ft.PopupMenuItem(),  # divider
        ft.PopupMenuItem(
            text="Back to kiosk",
            icon=ft.Icons.STORE_ROUNDED,
            on_click=lambda _e: page.go(Routes.HOME),
        ),
        ft.PopupMenuItem(
            text="Sign out",
            icon=ft.Icons.LOGOUT_ROUNDED,
            on_click=lambda _e: _logout(page),
        ),
    ]
    return ft.PopupMenuButton(
        icon=ft.Icons.MENU_ROUNDED,
        tooltip="Navigation",
        items=items,
    )


# ─────────────────────────────────────────────────────────────
#  FULL SIDEBAR
# ─────────────────────────────────────────────────────────────
def Sidebar(page: ft.Page, active_route: str) -> ft.Container:
    badges: dict = getattr(page, "_librai_admin_badges", {})

    # ── Logo mark ────────────────────────────────────────────
    logo = ft.Container(
        padding=ft.padding.only(bottom=Spacing.MD),
        content=ft.Row(
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                BrandLogo(52, 44, framed=True),
                ft.Column(
                    tight=True, spacing=1,
                    controls=[
                        ft.Text(APP_NAME, color=Colors.ON_PRIMARY,
                                weight=ft.FontWeight.W_800, size=16),
                        ft.Text(
                            settings.library_name,
                            color=Colors.SIDEBAR_TEXT_MUTED,
                            size=9,
                            width=118,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                ),
            ],
        ),
    )

    # ── Divider ──────────────────────────────────────────────
    def _divider() -> ft.Container:
        return ft.Container(
            height=1, bgcolor=Colors.SIDEBAR_DIVIDER,
            margin=ft.margin.symmetric(vertical=4),
        )

    # ── Nav item ──────────────────────────────────────────────
    def _nav_item(route: str, icon: str, label: str) -> ft.Control:
        active      = (route == active_route)
        badge_count = int(badges.get(route, 0))

        def hover(event: ft.ControlEvent) -> None:
            if active:
                return
            event.control.bgcolor = (
                Colors.SIDEBAR_SURFACE
                if str(event.data).lower() == "true"
                else ft.Colors.TRANSPARENT
            )
            event.control.update()

        trail: list[ft.Control] = []
        if badge_count:
            trail.append(
                ft.Container(
                    width=24,
                    border_radius=Radius.PILL,
                    bgcolor=Colors.ERROR,
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    alignment=ft.alignment.center,
                    content=ft.Text(str(badge_count), size=9,
                                    color=Colors.ON_PRIMARY,
                                    weight=ft.FontWeight.W_700),
                )
            )

        return ft.Container(
            border_radius=Radius.SM,
            bgcolor=Colors.SIDEBAR_ACTIVE if active else ft.Colors.TRANSPARENT,
            border=ft.border.only(
                left=ft.BorderSide(3, Colors.SIDEBAR_ACTIVE_BAR if active
                                   else ft.Colors.TRANSPARENT)
            ),
            padding=ft.padding.only(left=12, right=10, top=10, bottom=10),
            ink=False,
            animate=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
            on_hover=hover,
            on_click=lambda _e, r=route: None if r == active_route else page.go(r),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(
                        icon, size=17,
                        color=Colors.ON_PRIMARY if active else Colors.SIDEBAR_TEXT,
                    ),
                    ft.Text(
                        label,
                        expand=True,
                        size=13,
                        color=Colors.ON_PRIMARY if active else Colors.SIDEBAR_TEXT,
                        weight=ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL,
                    ),
                    *trail,
                ],
            ),
        )

    # ── Group label ───────────────────────────────────────────
    def _group_label(text: str) -> ft.Container:
        return ft.Container(
            padding=ft.padding.only(left=14, top=16, bottom=4),
            content=ft.Text(
                text, size=9, weight=ft.FontWeight.W_700,
                color=Colors.SIDEBAR_TEXT_MUTED,
            ),
        )

    # ── Assemble items ────────────────────────────────────────
    nav_controls: list[ft.Control] = [logo, _divider()]
    for g_label, items in GROUPS:
        nav_controls.append(_group_label(g_label))
        for route, icon, label in items:
            nav_controls.append(_nav_item(route, icon, label))

    # ── Footer ────────────────────────────────────────────────
    footer: list[ft.Control] = [
        ft.Container(expand=True),
        _divider(),
        ft.Container(
            border_radius=Radius.SM,
            padding=ft.padding.symmetric(horizontal=12, vertical=9),
            ink=False,
            on_click=lambda _e: page.go(Routes.HOME),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.STORE_OUTLINED, size=17,
                            color=Colors.SIDEBAR_TEXT_MUTED),
                    ft.Text("Kiosk view", size=13, color=Colors.SIDEBAR_TEXT_MUTED),
                ],
            ),
        ),
        ft.Container(
            border_radius=Radius.SM,
            padding=ft.padding.symmetric(horizontal=12, vertical=9),
            ink=False,
            on_click=lambda _e: _logout(page),
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Icon(ft.Icons.LOGOUT_ROUNDED, size=17,
                            color=Colors.SIDEBAR_TEXT_MUTED),
                    ft.Text("Sign out", size=13, color=Colors.SIDEBAR_TEXT_MUTED),
                ],
            ),
        ),
        ft.Container(height=4),
    ]

    return ft.Container(
        width=232,
        bgcolor=Colors.SIDEBAR_BG,
        padding=ft.padding.symmetric(horizontal=10, vertical=Spacing.MD),
        content=ft.Column(
            expand=True,
            spacing=2,
            controls=[*nav_controls, *footer],
        ),
    )


# ─────────────────────────────────────────────────────────────
#  ADMIN VIEW SHELL
# ─────────────────────────────────────────────────────────────
def AdminView(
    page: ft.Page,
    route: str,
    title: str,
    content: ft.Control,
    actions: list[ft.Control] | None = None,
    subtitle: str | None = None,
) -> ft.View:
    state   = get_state(page)
    admin   = state.admin_user or {}
    name    = str(admin.get("name") or admin.get("username") or "Staff")
    role    = str(admin.get("role") or "LIBRARIAN").replace("_", " ").title()
    compact = (getattr(page, "width", None) or 1366) < 1060

    # ── Server health indicator ───────────────────────────────
    checked = float(getattr(page, "_librai_health_checked_at", 0.0))
    if time.monotonic() - checked > 30:
        health = api_client.health()
        setattr(page, "_librai_api_online", health.ok)
        setattr(page, "_librai_health_checked_at", time.monotonic())
    online = bool(getattr(page, "_librai_api_online", False))

    health_pill = ft.Container(
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=Radius.PILL,
        bgcolor=Colors.SUCCESS_BG if online else Colors.ERROR_BG,
        border=ft.border.all(1, Colors.SUCCESS_MUTED if online else Colors.ERROR_BG),
        tooltip="Backend connected" if online else "Backend unreachable",
        content=ft.Row(
            tight=True, spacing=5,
            controls=[
                ft.Container(
                    width=6, height=6, border_radius=Radius.PILL,
                    bgcolor=Colors.SUCCESS if online else Colors.ERROR,
                ),
                *([] if compact else [
                    ft.Text(
                        "Online" if online else "Offline",
                        size=10, weight=ft.FontWeight.W_700,
                        color=Colors.SUCCESS if online else Colors.ERROR,
                    )
                ]),
            ],
        ),
    )

    # ── Identity badge ────────────────────────────────────────
    identity = ft.Row(
        tight=True, spacing=10,
        controls=[
            ft.Container(
                width=34, height=34,
                border_radius=Radius.PILL,
                bgcolor=Colors.PRIMARY_MUTED,
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.PERSON_ROUNDED, size=17, color=Colors.PRIMARY),
            ),
            *([] if compact else [
                ft.Column(
                    tight=True, spacing=1,
                    controls=[
                        ft.Text(name, size=13, weight=ft.FontWeight.W_700,
                                color=Colors.TEXT_PRIMARY),
                        ft.Text(role, size=10, color=Colors.TEXT_SECONDARY),
                    ],
                )
            ]),
        ],
    )

    # ── Page header ───────────────────────────────────────────
    title_col = ft.Column(
        tight=True, spacing=3,
        controls=[
            ft.Text(title, size=24 if compact else 26,
                    weight=ft.FontWeight.W_800, color=Colors.TEXT_PRIMARY),
            *([] if not subtitle else [
                ft.Text(subtitle, size=12, color=Colors.TEXT_SECONDARY),
            ]),
        ],
    )

    right_cluster = ft.Row(
        spacing=Spacing.SM,
        controls=[
            *(actions or []),
            ft.Container(width=1, height=28, bgcolor=Colors.BORDER),
            health_pill,
            ft.Container(width=1, height=28, bgcolor=Colors.BORDER),
            identity,
        ],
    )

    if compact:
        page_header: ft.Control = ft.Column(
            tight=True, spacing=Spacing.SM,
            controls=[
                ft.Row(
                    controls=[
                        AdminMenu(page, route),
                        ft.Container(width=8),
                        title_col,
                        ft.Container(expand=True),
                        health_pill,
                        identity,
                    ],
                ),
                *(
                    [ft.Row(wrap=True, spacing=8, run_spacing=8, controls=actions)]
                    if actions else []
                ),
            ],
        )
    else:
        page_header = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[title_col, right_cluster],
        )

    # ── Content area ─────────────────────────────────────────
    header_panel = ft.Container(
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.XL,
        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=18),
        shadow=Shadow.xs(),
        content=page_header,
    )

    workspace = ft.Container(
        expand=True,
        bgcolor=Colors.BACKGROUND,
        alignment=ft.alignment.top_center,
        padding=ft.padding.symmetric(
            horizontal=Spacing.MD if compact else Spacing.LG,
            vertical=Spacing.MD if compact else Spacing.LG,
        ),
        content=ft.Container(
            width=1560,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=Spacing.MD,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[header_panel, content, ft.Container(height=Spacing.SM)],
            ),
        ),
    )

    shell = (
        [workspace]
        if compact
        else [Sidebar(page, route), ft.VerticalDivider(width=1, color=Colors.BORDER), workspace]
    )

    return ft.View(
        route=route,
        padding=0,
        bgcolor=Colors.BACKGROUND,
        controls=[ft.Row(expand=True, spacing=0, controls=shell)],
    )
