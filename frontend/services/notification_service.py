"""Kiosk-safe in-system notification API operations."""

from services.api_client import api_client


class NotificationService:
    def list(self, user_id: int, verification_token: str):
        return api_client.get("/notifications", params={"user_id": user_id, "verification_token": verification_token})

    def mark_read(self, notification_id: int, verification_token: str):
        return api_client.post(f"/notifications/{notification_id}/read", {"verification_token": verification_token})


notification_service = NotificationService()
