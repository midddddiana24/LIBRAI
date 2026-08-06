from datetime import date
from services.api_client import ApiResult, api_client
from services.base import fallback


class ReturnService:
    def identify(self, copy_id: int, book_verification_token: str | None = None) -> ApiResult:
        data = {"id": 9, "copy_id": copy_id, "book_title": "Python Crash Course", "user_name": "Alex Dela Cruz", "student_id": "2023-00124", "due_at": date.today().isoformat(), "status": "borrowed"}
        return fallback(api_client.get(f"/borrowings/active/by-copy/{copy_id}", params={"book_verification_token": book_verification_token}), data)

    def create(self, borrowing_id: int, book_verification_token: str | None = None) -> ApiResult:
        data = {"id": "TXN-R-20260804-001", "book_title": "Python Crash Course", "returned_at": date.today().isoformat(), "return_status": "on_time"}
        return fallback(api_client.post("/returns", {"borrowing_id": borrowing_id, "book_verification_token": book_verification_token}), data)


return_service = ReturnService()
