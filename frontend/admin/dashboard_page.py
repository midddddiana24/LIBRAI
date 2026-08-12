"""
LIBRAI – Admin Dashboard
=========================
Executive summary of live library operations.
Layout: stat row → quick actions → bar chart + category panel → attention table
"""

from __future__ import annotations
from datetime import datetime
import flet as ft

from components.admin_ui import section_card, status_badge, page_intro
from components.alert    import Alert
from components.sidebar  import AdminView
from core.constants      import Routes
from core.theme          import Colors, Radius, Spacing, Shadow
from services.admin_service import admin_service


# ─────────────────────────────────────────────────────────────
#  METRIC CARD
# ─────────────────────────────────────────────────────────────
def _metric(
    label: str, value: int, icon: str, color: str, note: str
) -> ft.Container:
    return ft.Container(
        col={"sm": 12, "md": 6, "lg": 3},
        content=ft.Container(
            bgcolor=Colors.SURFACE,
            border=ft.border.all(1, Colors.BORDER),
            border_radius=Radius.LG,
            padding=Spacing.LG,
            shadow=Shadow.xs(),
            content=ft.Column(
                tight=True, spacing=Spacing.MD,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Container(
                                width=44, height=44,
                                border_radius=Radius.MD,
                                bgcolor=ft.Colors.with_opacity(0.10, color),
                                alignment=ft.alignment.center,
                                content=ft.Icon(icon, color=color, size=22),
                            ),
                            ft.Container(
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=Radius.PILL,
                                bgcolor=ft.Colors.with_opacity(0.08, color),
                                content=ft.Text(
                                    note, size=10, weight=ft.FontWeight.W_600,
                                    color=color,
                                ),
                            ),
                        ],
                    ),
                    ft.Column(
                        tight=True, spacing=3,
                        controls=[
                            ft.Text(f"{value:,}", size=30,
                                    weight=ft.FontWeight.W_800,
                                    color=Colors.TEXT_PRIMARY),
                            ft.Text(label, size=13,
                                    color=Colors.TEXT_SECONDARY),
                        ],
                    ),
                ],
            ),
        ),
    )


# ─────────────────────────────────────────────────────────────
#  BAR CHART
# ─────────────────────────────────────────────────────────────
def _bar_chart(activity: list[dict]) -> ft.Control:
    if not any(int(d.get("count", 0)) > 0 for d in activity):
        return ft.Container(
            height=160,
            alignment=ft.alignment.center,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.BAR_CHART_ROUNDED, size=36,
                            color=Colors.TEXT_DISABLED),
                    ft.Text("No activity yet", weight=ft.FontWeight.W_600,
                            color=Colors.TEXT_SECONDARY),
                    ft.Text("Completed transactions will appear here.",
                            size=12, color=Colors.TEXT_DISABLED),
                ],
            ),
        )

    peak = max(1, max(int(d.get("count", 0)) for d in activity))

    bars = []
    for d in activity:
        cnt   = int(d.get("count", 0))
        ratio = cnt / peak
        date  = str(d.get("date", ""))[-5:]  # MM-DD
        bars.append(
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.END,
                spacing=4,
                controls=[
                    ft.Text(str(cnt) if cnt else "", size=10,
                            color=Colors.TEXT_SECONDARY),
                    ft.Container(
                        width=28,
                        height=max(6, int(ratio * 100)),
                        bgcolor=Colors.PRIMARY if cnt else Colors.BORDER,
                        border_radius=ft.border_radius.only(
                            top_left=4, top_right=4),
                        tooltip=f"{cnt} borrowings",
                    ),
                    ft.Text(date, size=9, color=Colors.TEXT_DISABLED),
                ],
            )
        )

    return ft.Container(
        height=160,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.END,
            controls=bars,
        ),
    )


# ─────────────────────────────────────────────────────────────
#  CATEGORY BARS
# ─────────────────────────────────────────────────────────────
def _category_bars(categories: list[dict]) -> ft.Column:
    if not categories:
        return ft.Column(controls=[
            ft.Container(
                height=120, alignment=ft.alignment.center,
                content=ft.Text("No category data yet.",
                                color=Colors.TEXT_SECONDARY, size=13),
            )
        ])

    peak = max(1, max(int(c.get("count", 0)) for c in categories))
    rows: list[ft.Control] = []
    for c in categories[:6]:
        cnt   = int(c.get("count", 0))
        label = str(c.get("category", "Unknown"))
        rows.append(
            ft.Column(
                tight=True, spacing=5,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(label, size=12, color=Colors.TEXT_PRIMARY,
                                    expand=True, max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(str(cnt), size=12,
                                    weight=ft.FontWeight.W_700,
                                    color=Colors.PRIMARY),
                        ],
                    ),
                    ft.ProgressBar(
                        value=cnt / peak,
                        color=Colors.PRIMARY_LIGHT,
                        bgcolor=Colors.PRIMARY_MUTED,
                        height=5,
                        border_radius=Radius.PILL,
                    ),
                ],
            )
        )

    return ft.Column(tight=True, spacing=12, controls=rows)


# ─────────────────────────────────────────────────────────────
#  BUILD
# ─────────────────────────────────────────────────────────────
def build(page: ft.Page) -> ft.View:
    result = admin_service.dashboard()
    if not result.ok:
        return AdminView(
            page, Routes.ADMIN_DASHBOARD, "Dashboard",
            Alert(result.error_kind, result.message),
        )

    data = result.data
    available    = int(data.get("available_copies",   data.get("available_books",  0)))
    borrowed     = int(data.get("borrowed_copies",    data.get("borrowed_books",   0)))
    overdue      = int(data.get("overdue_borrowings", data.get("overdue_books",    0)))
    reservations = int(data.get("active_reservations",data.get("reservations",     0)))

    setattr(page, "_librai_admin_badges", {
        Routes.ADMIN_BORROWINGS:   overdue,
        Routes.ADMIN_RESERVATIONS: reservations,
    })

    # ── Date + summary banner ─────────────────────────────────
    today = datetime.now().strftime("%A, %B %d, %Y")
    transactions_today = int(data.get("transactions_today", 0))

    banner = ft.Container(
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.LG,
        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.MD),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    expand=True,
                    spacing=Spacing.MD,
                    controls=[
                        ft.Container(
                            width=40, height=40,
                            border_radius=Radius.MD,
                            bgcolor=Colors.SUCCESS_BG,
                            alignment=ft.alignment.center,
                            content=ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                                            size=20, color=Colors.SUCCESS),
                        ),
                        ft.Column(
                            tight=True, spacing=2,
                            controls=[
                                ft.Text("Library Operations Overview",
                                        size=14, weight=ft.FontWeight.W_700),
                                ft.Text("Live circulation and inventory data.",
                                        size=11, color=Colors.TEXT_SECONDARY),
                            ],
                        ),
                    ],
                ),
                ft.Container(
                    width=255,
                    bgcolor=Colors.SURFACE_ALT,
                    border=ft.border.all(1, Colors.BORDER),
                    border_radius=Radius.MD,
                    padding=ft.padding.symmetric(horizontal=Spacing.MD, vertical=10),
                    content=ft.Row(
                        spacing=Spacing.SM,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                width=34, height=34,
                                border_radius=Radius.SM,
                                bgcolor=Colors.PRIMARY_MUTED,
                                alignment=ft.alignment.center,
                                content=ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, size=18, color=Colors.PRIMARY),
                            ),
                            ft.Column(
                                expand=True,
                                tight=True,
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                controls=[
                                    ft.Text(today, size=11, weight=ft.FontWeight.W_600,
                                            color=Colors.TEXT_PRIMARY, text_align=ft.TextAlign.RIGHT),
                                    ft.Text(f"{transactions_today:,} transaction{'s' if transactions_today != 1 else ''} today",
                                            size=11, color=Colors.TEXT_SECONDARY,
                                            text_align=ft.TextAlign.RIGHT),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    # ── Stat row ──────────────────────────────────────────────
    metrics = ft.ResponsiveRow(
        spacing=Spacing.MD, run_spacing=Spacing.MD,
        controls=[
            _metric("Available Copies",    available,    ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED, Colors.SUCCESS, "Ready"),
            _metric("Currently Borrowed",  borrowed,     ft.Icons.OUTPUT_ROUNDED,               Colors.PRIMARY, "Active"),
            _metric("Overdue Items",       overdue,      ft.Icons.WARNING_AMBER_ROUNDED,        Colors.ERROR,   "Urgent"),
            _metric("Reservations",        reservations, ft.Icons.BOOKMARK_BORDER_ROUNDED,      Colors.WARNING, "Queued"),
        ],
    )

    # ── Quick actions ─────────────────────────────────────────
    def _action_btn(label: str, icon: str, route: str,
                    filled: bool = False) -> ft.Control:
        if filled:
            return ft.FilledButton(label, icon=icon,
                                   on_click=lambda _e: page.go(route))
        return ft.OutlinedButton(label, icon=icon,
                                 on_click=lambda _e: page.go(route))

    quick_actions = section_card(
        title="Quick Actions",
        content=ft.Row(
            wrap=True, spacing=Spacing.SM, run_spacing=Spacing.SM,
            controls=[
                _action_btn("Add Book",       ft.Icons.ADD_ROUNDED,               Routes.ADMIN_BOOKS,        filled=True),
                _action_btn("Register User",  ft.Icons.PERSON_ADD_ALT_ROUNDED,    Routes.ADMIN_USERS),
                _action_btn("Review Returns", ft.Icons.KEYBOARD_RETURN_ROUNDED,   Routes.ADMIN_RETURNS),
                _action_btn("Reports",        ft.Icons.DOWNLOAD_OUTLINED,         Routes.ADMIN_REPORTS),
            ],
        ),
    )

    # ── Chart ─────────────────────────────────────────────────
    chart = section_card(
        title="Borrowing Activity",
        subtitle="Last 7 days",
        content=_bar_chart(data.get("borrowings_by_day", [])),
        height=260,
    )

    # ── Categories ────────────────────────────────────────────
    categories = section_card(
        title="Popular Categories",
        content=_category_bars(data.get("popular_categories", [])),
        height=260,
    )

    insights = ft.ResponsiveRow(
        spacing=Spacing.MD, run_spacing=Spacing.MD,
        controls=[
            ft.Container(col={"sm": 12, "lg": 8}, content=chart),
            ft.Container(col={"sm": 12, "lg": 4}, content=categories),
        ],
    )

    unmet = data.get("unmet_searches", [])
    demand_insights = section_card(
        title="Catalog Demand & AI Quality",
        subtitle="Use unmet searches to guide acquisitions and monitor recommendation reliability.",
        content=ft.ResponsiveRow(
            spacing=Spacing.MD,
            run_spacing=Spacing.MD,
            controls=[
                ft.Container(
                    col={"sm":12,"lg":8},
                    content=ft.Column(
                        tight=True,
                        spacing=Spacing.SM,
                        controls=[
                            *([ft.Row(controls=[ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED,size=16,color=Colors.WARNING),ft.Text(str(row.get("query","")),expand=True),ft.Text(f"{row.get('searches',0)} searches",size=11,color=Colors.TEXT_SECONDARY)]) for row in unmet] or [ft.Text("No repeated zero-result searches yet.",color=Colors.TEXT_SECONDARY)]),
                        ],
                    ),
                ),
                ft.Container(
                    col={"sm":12,"lg":4},
                    bgcolor=Colors.SURFACE_ALT,
                    border_radius=Radius.MD,
                    padding=Spacing.MD,
                    content=ft.Column(tight=True,spacing=6,controls=[ft.Text("AI service quality",weight=ft.FontWeight.W_700),ft.Text(f"Fallback rate: {data.get('ai_fallback_rate',0)}%",size=12,color=Colors.TEXT_SECONDARY),ft.Text("Helpful rating: No feedback yet" if data.get("ai_helpful_rate") is None else f"Helpful rating: {data.get('ai_helpful_rate')}%",size=12,color=Colors.TEXT_SECONDARY),ft.Text(f"Renewals today: {data.get('renewals_today',0)}",size=12,color=Colors.TEXT_SECONDARY)]),
                ),
            ],
        ),
    )

    # ── Attention rows ────────────────────────────────────────
    attention_rows = [
        ("Overdue Items",      overdue,      "overdue"   if overdue      else "active", Routes.ADMIN_BORROWINGS),
        ("Reservation Queue",  reservations, "reserved"  if reservations else "active", Routes.ADMIN_RESERVATIONS),
        ("Unpaid Fines",       int(data.get("unpaid_fines", 0)), "overdue" if data.get("unpaid_fines", 0) else "active", Routes.ADMIN_FINES),
        ("Failed Email Queue", int(data.get("failed_email_deliveries", 0)), "overdue" if data.get("failed_email_deliveries", 0) else "active", Routes.ADMIN_EMAIL_DELIVERIES),
    ]

    attention = section_card(
        title="Attention Required",
        content=ft.Column(
            tight=True, spacing=0,
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10),
                    border=ft.border.only(bottom=ft.BorderSide(
                        0.8 if i < len(attention_rows) - 1 else 0,
                        Colors.BORDER)),
                    content=ft.Row(
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(
                                ft.Icons.WARNING_AMBER_ROUNDED
                                if count > 0 else ft.Icons.CHECK_CIRCLE_OUTLINE_ROUNDED,
                                size=16,
                                color=Colors.ERROR if count > 0 else Colors.SUCCESS,
                            ),
                            ft.Container(width=8),
                            ft.Text(label, expand=True, size=13,
                                    color=Colors.TEXT_PRIMARY),
                            ft.Text(f"{count:,}", size=14,
                                    weight=ft.FontWeight.W_700,
                                    color=Colors.ERROR if count > 0
                                    else Colors.TEXT_SECONDARY),
                            ft.Container(width=8),
                            status_badge(status),
                            ft.Container(width=4),
                            ft.IconButton(
                                ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                icon_size=13,
                                tooltip=f"View {label.lower()}",
                                style=ft.ButtonStyle(enable_feedback=False),
                                on_click=lambda _e, r=route: page.go(r),
                            ),
                        ],
                    ),
                )
                for i, (label, count, status, route) in enumerate(attention_rows)
            ],
        ),
    )

    # ── Footer stats ──────────────────────────────────────────
    footer_stats = ft.Row(
        wrap=True, spacing=Spacing.XL,
        controls=[
            _stat_pill(ft.Icons.LIBRARY_BOOKS_OUTLINED,
                       f"{int(data.get('total_books', 0)):,} catalog titles"),
            _stat_pill(ft.Icons.COPY_ALL_OUTLINED,
                       f"{int(data.get('total_copies', 0)):,} physical copies"),
            _stat_pill(ft.Icons.GROUP_OUTLINED,
                       f"{int(data.get('registered_users', 0)):,} registered users"),
        ],
    )

    content = ft.Column(
        tight=True, spacing=Spacing.LG,
        controls=[banner, metrics, insights, quick_actions, attention, demand_insights, footer_stats],
    )

    return AdminView(page, Routes.ADMIN_DASHBOARD, "Dashboard", content,
                     subtitle="Library operations overview")


def _stat_pill(icon: str, label: str) -> ft.Row:
    return ft.Row(
        spacing=6,
        tight=True,
        controls=[
            ft.Icon(icon, size=14, color=Colors.TEXT_DISABLED),
            ft.Text(label, size=12, color=Colors.TEXT_SECONDARY),
        ],
    )
