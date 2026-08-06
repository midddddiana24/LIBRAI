from services.api_client import api_client
from services.base import fallback
from services.book_service import _MOCK_BOOKS


class AIService:
    def search(self, query: str, user_id=None, user_verification_token=None):
        data = {"answer": "These available library books best match your request.", "books": [b for b in _MOCK_BOOKS if b["available_copies"] > 0], "query": query}
        return fallback(api_client.post("/ai/search", {"query": query, "user_id": user_id, "user_verification_token": user_verification_token}), data)

    def recommend(self, user_id=None, kind="personalized", user_verification_token=None):
        return fallback(api_client.post("/ai/recommend", {"user_id": user_id, "kind": kind, "user_verification_token": user_verification_token}), _MOCK_BOOKS)

    def feedback(self, interaction_id: int, helpful: bool, user_id=None, user_verification_token=None):
        return api_client.post("/ai/feedback", {"interaction_id": interaction_id, "helpful": helpful, "user_id": user_id, "user_verification_token": user_verification_token})


ai_service = AIService()
