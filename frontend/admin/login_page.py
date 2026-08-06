"""
LIBRAI – Admin Login Page
==========================
Elegant, centered login card on a subtle patterned background.
School-library theme: deep navy logo, gold accent, clean form.
"""

from __future__ import annotations
import flet as ft

from components.admin_ui import admin_text_field
from components.alert    import Alert
from components.brand_logo import BrandLogo
from core.constants      import Routes
from core.state          import get_state
from core.theme          import Colors, Radius, Spacing, Shadow
from services.auth_service import auth_service


def build(page: ft.Page) -> ft.View:
    state = get_state(page)

    username = admin_text_field(
        label="Username or e-mail",
        autofocus=True,
        prefix_icon=ft.Icons.PERSON_OUTLINE_ROUNDED,
    )
    password = admin_text_field(
        label="Password",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK_OUTLINE_ROUNDED,
    )
    notice = ft.Column(tight=True, spacing=0)
    saved_notice = getattr(page, "_librai_admin_login_notice", None)
    if saved_notice:
        notice.controls.append(Alert("auth_error", str(saved_notice), title="Staff session ended"))
        setattr(page, "_librai_admin_login_notice", None)
    loading = ft.ProgressBar(
        color=Colors.BRAND_GREEN, bgcolor=Colors.PRIMARY_MUTED, height=3,
        visible=False,
    )
    submit_btn = ft.FilledButton(
        "Sign in",
        icon=ft.Icons.LOGIN_ROUNDED,
        width=380,
    )

    def login(_e) -> None:
        notice.controls.clear()
        if not username.value or not password.value:
            notice.controls.append(
                Alert("validation_error", "Please enter your username and password.")
            )
            page.update()
            return

        loading.visible = True
        submit_btn.disabled = True
        submit_btn.text = "Signing in…"
        page.update()

        r = auth_service.login(username.value.strip(), password.value)

        loading.visible = False
        submit_btn.disabled = False
        submit_btn.text = "Sign in"

        if r.ok:
            state.admin_user = r.data.get("user", {})
            state.admin_token = r.data.get("access_token")
            page.client_storage.set("librai_admin_user",  state.admin_user)
            page.client_storage.set("librai_admin_token", r.data.get("access_token"))
            page.go(Routes.ADMIN_DASHBOARD)
        else:
            notice.controls.append(
                Alert(
                    r.error_kind,
                    r.message,
                    title="Login failed" if r.status_code == 401 else None,
                )
            )
            page.update()

    submit_btn.on_click = login
    password.on_submit  = login

    # ── Card ─────────────────────────────────────────────────
    card = ft.Container(
        width=430,
        bgcolor=Colors.SURFACE,
        border_radius=Radius.XL,
        border=ft.border.all(1, Colors.BORDER),
        shadow=Shadow.md(),
        padding=ft.padding.symmetric(horizontal=Spacing.XXL, vertical=Spacing.XL + 8),
        content=ft.Column(
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=Spacing.MD,
            controls=[
                # ── Logo ──────────────────────────────────────
                ft.Container(
                    width=62, height=4, border_radius=Radius.PILL,
                    bgcolor=Colors.BRAND_GREEN,
                ),
                BrandLogo(170, 116),
                # ── Heading ───────────────────────────────────
                ft.Column(
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Text("Administration Portal", size=21, weight=ft.FontWeight.W_800,
                                color=Colors.TEXT_PRIMARY),
                        ft.Text("Secure access for authorized library staff", size=13,
                                color=Colors.TEXT_SECONDARY,
                                text_align=ft.TextAlign.CENTER),
                    ],
                ),
                ft.Container(height=4),
                # ── Divider ───────────────────────────────────
                ft.Container(height=1, bgcolor=Colors.BORDER),
                ft.Container(height=4),
                ft.Text("Welcome back", size=17, weight=ft.FontWeight.W_700,
                        color=Colors.TEXT_PRIMARY),
                ft.Text(
                    "Use your authorized library staff credentials to continue.",
                    size=12, color=Colors.TEXT_SECONDARY,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=4),
                # ── Form ──────────────────────────────────────
                username,
                password,
                loading,
                notice,
                ft.Container(height=4),
                submit_btn,
                ft.Container(height=4),
                # ── Footer ────────────────────────────────────
                ft.Container(
                    alignment=ft.alignment.center,
                    content=ft.TextButton(
                        "← Return to kiosk",
                        style=ft.ButtonStyle(
                            color=Colors.TEXT_SECONDARY,
                            enable_feedback=False,
                        ),
                        on_click=lambda _e: page.go(Routes.HOME),
                    ),
                ),
            ],
        ),
    )

    # ── Background panel (left brand stripe) ─────────────────
    bg = ft.Container(
        expand=True,
        bgcolor=Colors.BACKGROUND,
        content=ft.Row(
            expand=True,
            spacing=0,
            controls=[
                # Brand panel
                ft.Container(
                    width=360,
                    bgcolor=Colors.PRIMARY_DARK,
                    alignment=ft.alignment.center,
                    visible=False,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=Spacing.MD,
                        controls=[
                            ft.Icon(ft.Icons.LOCAL_LIBRARY_ROUNDED,
                                    size=48, color=Colors.GOLD),
                            ft.Text("LIBRAI", size=26, weight=ft.FontWeight.W_800,
                                    color=Colors.ON_PRIMARY),
                            ft.Container(
                                width=200,
                                content=ft.Text(
                                    "AI-Powered Library Management System",
                                    size=13, color=Colors.SIDEBAR_TEXT,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ),
                            ft.Container(height=Spacing.LG),
                            ft.Container(
                                padding=ft.padding.all(Spacing.MD),
                                border_radius=Radius.MD,
                                bgcolor=ft.Colors.with_opacity(0.12, Colors.ON_PRIMARY),
                                content=ft.Column(
                                    tight=True, spacing=6,
                                    controls=[
                                        _feature_row(ft.Icons.QR_CODE_SCANNER_ROUNDED, "QR borrowing & returns"),
                                        _feature_row(ft.Icons.AUTO_AWESOME_ROUNDED,    "AI book recommendations"),
                                        _feature_row(ft.Icons.INSIGHTS_ROUNDED,        "Real-time dashboard"),
                                        _feature_row(ft.Icons.HISTORY_ROUNDED,         "Full audit trail"),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ),
                # Card area
                ft.Container(
                    expand=True,
                    alignment=ft.alignment.center,
                    bgcolor=Colors.BACKGROUND,
                    content=card,
                ),
            ],
        ),
    )

    return ft.View(
        route=Routes.ADMIN_LOGIN,
        padding=0,
        bgcolor=Colors.BACKGROUND,
        controls=[bg],
    )


def _feature_row(icon: str, label: str) -> ft.Row:
    return ft.Row(
        spacing=10,
        controls=[
            ft.Icon(icon, size=14, color=Colors.GOLD),
            ft.Text(label, size=12, color=Colors.SIDEBAR_TEXT),
        ],
    )
