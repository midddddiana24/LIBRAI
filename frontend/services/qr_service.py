from services.api_client import ApiResult, api_client
from services.base import fallback

MOCK_USER = {"id": 1, "name": "Alex Dela Cruz", "student_id": "2023-00124", "course": "BS Information Technology", "year_level": "3", "account_status": "active", "current_borrowed_count": 1, "borrowing_limit": 5, "has_overdue": False}
MOCK_COPY = {"id": 11, "copy_id": "BK-0001-C01", "book_id": 1, "title": "Python Crash Course", "author": "Eric Matthes", "category": "Computer Science", "shelf_location": "CS-104", "available": True, "cover_url": None}


class QRService:
    def decode_image(self, file_path: str) -> ApiResult:
        return api_client.upload_file("/qr/decode-image", file_path)

    def verify_user(self, token: str) -> ApiResult:
        return fallback(api_client.post("/qr/verify-user", {"token": token}), MOCK_USER)

    def verify_book(self, token: str) -> ApiResult:
        return fallback(api_client.post("/qr/verify-book", {"token": token}), MOCK_COPY)


qr_service = QRService()
