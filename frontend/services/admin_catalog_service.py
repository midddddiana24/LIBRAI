"""Administrative catalog and member API operations."""

from __future__ import annotations

from services.api_client import api_client


class AdminCatalogService:
    @staticmethod
    def _download_ready(result):
        if result.ok and isinstance(result.data, dict) and result.data.get("download_url"):
            result.data["download_url"] = api_client.resolve_url(result.data["download_url"])
        return result
    def list_books(self, query: str | None = None, category: str | None = None, author: str | None = None, shelf_location: str | None = None, available_only: bool = False, offset: int = 0, limit: int = 25, include_archived: bool = False):
        return api_client.get(
            "/books",
            params={"q": query or None, "category": category or None, "author": author or None, "shelf_location": shelf_location or None, "available_only": available_only, "offset": offset, "limit": limit, "include_archived": include_archived},
        )

    def export_books(self):
        return api_client.get("/books/export.csv")

    def import_books(self, file_path: str):
        return api_client.upload_file("/books/import.csv", file_path)

    def create_book(self, payload: dict):
        return api_client.post("/books", payload)

    def update_book(self, book_id: int, payload: dict):
        return api_client.put(f"/books/{book_id}", payload)

    def upload_book_cover(self, book_id: int, file_path: str):
        return api_client.upload_file(f"/books/{book_id}/cover", file_path)

    def archive_book(self, book_id: int):
        return api_client.post(f"/books/{book_id}/archive", {})

    def list_copies(self, book_id: int):
        return api_client.get(f"/books/{book_id}/copies")

    def add_copies(self, book_id: int, quantity: int, accession_numbers: list[str] | None = None):
        return api_client.post(
            f"/books/{book_id}/copies",
            {"quantity": quantity, "accession_numbers": accession_numbers or None},
        )

    def create_copy_qr_sheet(self, book_id: int):
        result = api_client.post(f"/books/{book_id}/copies/qr-sheet", {})
        if result.ok and isinstance(result.data, dict) and result.data.get("download_url"):
            result.data["download_url"] = api_client.resolve_url(result.data["download_url"])
        return result

    def update_copy_status(self, copy_id: int, status: str):
        return api_client.put(f"/book-copies/{copy_id}", {"status": status})

    def rotate_copy_qr(self, copy_id: int):
        return self._download_ready(api_client.post(f"/book-copies/{copy_id}/qr", {}))

    def get_copy_qr(self, copy_id: int):
        return self._download_ready(api_client.get(f"/book-copies/{copy_id}/qr"))

    def list_users(self, query: str | None = None, offset: int = 0, limit: int = 25):
        return api_client.get("/users", params={"q": query or None, "offset": offset, "limit": limit})

    def create_user(self, payload: dict):
        return api_client.post("/users", payload)

    def update_user(self, user_id: int, payload: dict):
        return api_client.put(f"/users/{user_id}", payload)

    def upload_user_photo(self, user_id: int, file_path: str):
        return api_client.upload_file(f"/users/{user_id}/photo", file_path)

    def rotate_user_qr(self, user_id: int):
        return self._download_ready(api_client.post(f"/users/{user_id}/qr", {}))

    def get_user_qr(self, user_id: int):
        return self._download_ready(api_client.get(f"/users/{user_id}/qr"))

    def user_borrowings(self, user_id: int):
        return api_client.get("/borrowings", params={"user_id": user_id, "limit": 100})


admin_catalog_service = AdminCatalogService()
