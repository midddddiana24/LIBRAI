from services.api_client import api_client
from services.base import fallback


class ReservationService:
    def list(self, user_id=None, verification_token=None):
        params = {"user_id": user_id, "verification_token": verification_token} if user_id else None
        return fallback(api_client.get("/reservations", params=params), [])

    def create(self, user_id: int, book_id: int, verification_token=None):
        return fallback(api_client.post("/reservations", {"user_id": user_id, "book_id": book_id, "user_verification_token": verification_token}), {"id": 1, "status": "active", "position": 1})

    def cancel(self, reservation_id: int, verification_token=None):
        return api_client.delete(f"/reservations/{reservation_id}", params={"verification_token": verification_token})


reservation_service = ReservationService()
