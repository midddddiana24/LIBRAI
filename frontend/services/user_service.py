from services.api_client import api_client
from services.base import fallback
from services.qr_service import MOCK_USER


class UserService:
    def list(self, **params):
        return fallback(api_client.get("/users", params=params), [MOCK_USER])

    def get(self, user_id):
        return fallback(api_client.get(f"/users/{user_id}"), MOCK_USER)

    def create(self, payload):
        return api_client.post("/users", payload)

    def update(self, user_id, payload):
        return api_client.put(f"/users/{user_id}", payload)


user_service = UserService()
