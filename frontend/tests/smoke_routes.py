"""Fast constructor smoke test for all frontend routes (no Flet server needed)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("LIBRAI_API_TIMEOUT_SECONDS", "1")

from core.constants import Routes
from core.routes import build_view
from core.state import get_state
from services.qr_service import MOCK_COPY, MOCK_USER
from services.admin_service import admin_service
from services.admin_catalog_service import admin_catalog_service
from services.api_client import ApiResult


class Storage:
    def __init__(self): self.values = {}
    def get(self, key): return self.values.get(key)
    def set(self, key, value): self.values[key] = value
    def remove(self, key): self.values.pop(key, None)


class PageStub:
    def __init__(self):
        self.route = Routes.HOME
        self.client_storage = Storage()
        self.overlay = []
    def go(self, route): self.route = route
    def update(self): pass
    def open(self, _control): pass
    def close(self, _control): pass


def main() -> None:
    page = PageStub()
    state = get_state(page)
    public_routes = [Routes.HOME, Routes.SEARCH, Routes.AI_ASSISTANT, Routes.RECOMMENDATIONS, Routes.POPULAR_BOOKS, Routes.NEW_BOOKS, Routes.ACCOUNT, Routes.RESERVATIONS, Routes.BORROW_SCAN_USER, Routes.RETURN_SCAN_BOOK, Routes.ADMIN_LOGIN]
    for route in public_routes:
        page.route = route
        build_view(route, page)

    state.kiosk_user = MOCK_USER.copy()
    state.scanned_book = MOCK_COPY.copy()
    state.active_borrowing = {"id": 1, "book_title": "Test", "user_name": "Test User", "student_id": "1", "due_at": "2026-08-04"}
    state.last_transaction = {"id": "T-1", "book_title": "Test", "borrowed_at": "2026-08-04", "due_at": "2026-08-18", "returned_at": "2026-08-04", "return_status": "on_time"}
    workflow_routes = [Routes.BORROW_USER_VERIFIED, Routes.BORROW_SCAN_BOOK, Routes.BORROW_CONFIRM, Routes.BORROW_SUCCESS, Routes.RETURN_CONFIRM, Routes.RETURN_SUCCESS, f"{Routes.BOOK_DETAILS}/1"]
    for route in workflow_routes:
        page.route = route
        build_view(route, page)

    state.admin_user = {"name": "Test Admin", "role": "admin"}
    state.admin_token = "route-smoke-token"
    original_dashboard = admin_service.dashboard
    admin_service.dashboard = lambda: ApiResult.success({
        "total_books": 12, "total_copies": 24, "available_books": 18,
        "borrowed_books": 6, "overdue_books": 2, "registered_users": 30,
        "transactions_today": 4, "reservations": 3,
        "borrowings_by_day": [{"date": "2026-08-05", "count": 4}],
        "popular_categories": [{"category": "Technology", "count": 4}],
    })
    page.route = Routes.ADMIN_DASHBOARD
    build_view(Routes.ADMIN_DASHBOARD, page)._build_add_commands()
    admin_service.dashboard = original_dashboard
    original_books = admin_catalog_service.list_books
    original_users = admin_catalog_service.list_users
    admin_catalog_service.list_books = lambda *args, **kwargs: ApiResult.success({"items": [{"id": 1, "isbn": "9780000000001", "title": "Test Book", "author": "Test Author", "category": "Technology", "available_copies": 1, "total_copies": 2, "shelf_location": "A-01", "is_archived": False}], "total": 1})
    admin_catalog_service.list_users = lambda *args, **kwargs: ApiResult.success({"items": [{"id": 1, "display_name": "Test Student", "student_id": "2026-0001", "course": "BSIT", "year_level": "3", "email": "student@example.test", "active_borrowing_count": 1, "has_overdue_books": False, "status": "active"}], "total": 1})
    build_view(Routes.ADMIN_BOOKS, page)._build_add_commands()
    build_view(Routes.ADMIN_USERS, page)._build_add_commands()
    admin_catalog_service.list_books = original_books
    admin_catalog_service.list_users = original_users
    admin_routes = [Routes.ADMIN_DASHBOARD, Routes.ADMIN_BOOKS, Routes.ADMIN_USERS, Routes.ADMIN_BORROWINGS, Routes.ADMIN_RETURNS, Routes.ADMIN_RESERVATIONS, Routes.ADMIN_REPORTS, Routes.ADMIN_AUDIT_LOGS, Routes.ADMIN_SETTINGS]
    for route in admin_routes:
        page.route = route
        build_view(route, page)
    print(f"ROUTE_SMOKE_OK {len(public_routes) + len(workflow_routes) + len(admin_routes)}")


if __name__ == "__main__": main()
