"""LIBRAI Flet application entry point."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path

import flet as ft

from components.loading_view import BrandedLoadingView
from core.config import settings
from core.constants import Routes, Session
from core.routes import build_view
from core.state import get_state
from core.theme import Colors, build_admin_theme, build_theme


def main(page: ft.Page) -> None:
    state = get_state(page)
    page.title = "LIBRAI — AI-Powered Library Kiosk"
    kiosk_theme = build_theme()
    admin_theme = build_admin_theme()
    page.theme = kiosk_theme
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = Colors.BACKGROUND
    page.padding = 0
    page.window.width = settings.window_width
    page.window.height = settings.window_height
    page.window.full_screen = settings.fullscreen

    def route_change(_event) -> None:
        state.touch()
        page.theme = admin_theme if page.route.startswith("/admin") else kiosk_theme
        loading_routes = {
            Routes.SEARCH,
            Routes.RECOMMENDATIONS,
            Routes.NEW_BOOKS,
            Routes.POPULAR_BOOKS,
            Routes.ACCOUNT,
            Routes.RESERVATIONS,
        }
        if page.route.startswith("/admin/") and page.route != Routes.ADMIN_LOGIN:
            loading_routes.add(page.route)
        if page.route in loading_routes or page.route.startswith("/book/"):
            page.views.clear()
            page.views.append(BrandedLoadingView(page.route))
            page.update()
        page.views.clear()
        page.views.append(build_view(page.route, page))
        page.update()

    def view_pop(_event) -> None:
        page.go("/")

    async def enforce_kiosk_privacy() -> None:
        """Reset private kiosk state after the configured inactivity period."""
        while True:
            await asyncio.sleep(5)
            elapsed = (datetime.now() - state.last_activity).total_seconds()
            private_session = state.kiosk_user is not None or bool(state.ai_messages)
            warning_at = Session.INACTIVITY_TIMEOUT_SECONDS - Session.WARNING_BEFORE_RESET_SECONDS
            if private_session and elapsed >= warning_at and not state.timeout_warning_shown:
                state.timeout_warning_shown = True
                remaining = max(1, int(Session.INACTIVITY_TIMEOUT_SECONDS - elapsed))
                warning = ft.SnackBar(
                    content=ft.Text(f"For your privacy, this session will end in about {remaining} seconds."),
                    action="Keep session",
                    on_action=lambda _event: state.touch(),
                    duration=Session.WARNING_BEFORE_RESET_SECONDS * 1000,
                    bgcolor=Colors.PRIMARY_DARK,
                )
                page.open(warning)
            if private_session and elapsed >= Session.INACTIVITY_TIMEOUT_SECONDS:
                state.clear_kiosk()
                page.client_storage.set("librai_voice_enabled", "false")
                page.client_storage.remove("librai_voice_mode")
                page.go(Routes.HOME)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.run_task(enforce_kiosk_privacy)
    page.go(page.route or "/")


if __name__ == "__main__":
    os.environ.setdefault("FLET_SECRET_KEY", settings.flet_secret_key)
    settings.frontend_upload_directory.mkdir(parents=True, exist_ok=True)
    ft.app(
        target=main,
        upload_dir=str(settings.frontend_upload_directory),
        assets_dir=str(Path(__file__).parent / "assets"),
    )
