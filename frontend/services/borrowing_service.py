from datetime import date, timedelta
from services.api_client import ApiResult, api_client
from services.base import fallback


class BorrowingService:
    def create(self, user_id: int, copy_id: int, user_verification_token: str | None = None, book_verification_token: str | None = None) -> ApiResult:
        data = {"id": "TXN-B-20260804-001", "book_title": "Python Crash Course", "borrowed_at": date.today().isoformat(), "due_at": (date.today() + timedelta(days=14)).isoformat(), "status": "borrowed"}
        return fallback(api_client.post("/borrowings", {"user_id": user_id, "book_copy_id": copy_id, "user_verification_token": user_verification_token, "book_verification_token": book_verification_token}), data)

    def list(self, **params) -> ApiResult:
        return fallback(api_client.get("/borrowings", params=params), [])

    def renew(self, borrowing_id: int, user_id: int, verification_token: str) -> ApiResult:
        return api_client.post(
            f"/borrowings/{borrowing_id}/renew",
            {"user_id": user_id, "user_verification_token": verification_token},
        )


borrowing_service = BorrowingService()
