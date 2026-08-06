from __future__ import annotations
from admin import books_page, dashboard_page, login_page, management_page, reports_page, settings_page, users_page
from core.constants import Routes
from core.state import get_state
from services.auth_service import auth_service

CONFIG={
 Routes.ADMIN_BORROWINGS:("Borrowings","/borrowings","Monitor active and historical borrowing transactions.",False),
 Routes.ADMIN_RETURNS:("Returns","/returns","Review completed book return transactions.",False),
 Routes.ADMIN_RESERVATIONS:("Reservations","/reservations","Monitor reservation queues and availability.",False),
 Routes.ADMIN_AUDIT_LOGS:("Audit Logs","/audit-logs","Review security-sensitive administrative activity.",False),
}


def build_view(route,page):
    state = get_state(page)
    if route==Routes.ADMIN_LOGIN:return login_page.build(page)
    stored_user=page.client_storage.get("librai_admin_user")
    stored_token=page.client_storage.get("librai_admin_token")
    token=state.admin_token or stored_token
    if not state.admin_user and stored_user:
        state.admin_user=stored_user
    if not state.admin_user or not token:
        return login_page.build(page)

    # Route changes and Flet event handlers can execute in different Python
    # contexts. Restore the page-owned token before every protected page is
    # built so a successful login never becomes a false "session expired".
    auth_service.restore_token(token)
    if state.admin_token is None:
        restored=auth_service.current_admin()
        if not restored.ok:
            state.admin_user=None
            state.admin_token=None
            auth_service.restore_token(None)
            page.client_storage.remove("librai_admin_user")
            page.client_storage.remove("librai_admin_token")
            setattr(page,"_librai_admin_login_notice","Your saved staff session expired. Please sign in again.")
            return login_page.build(page)
        state.admin_user=restored.data
        state.admin_token=token
        page.client_storage.set("librai_admin_user",state.admin_user)
    if route==Routes.ADMIN_DASHBOARD:return dashboard_page.build(page)
    if route==Routes.ADMIN_BOOKS:return books_page.build(page)
    if route==Routes.ADMIN_USERS:return users_page.build(page)
    if route==Routes.ADMIN_REPORTS:return reports_page.build(page)
    if route==Routes.ADMIN_SETTINGS:return settings_page.build(page)
    if route in CONFIG:
        title,endpoint,description,add=CONFIG[route]
        return management_page.build(page,route,title,endpoint,description,add)
    return dashboard_page.build(page)
