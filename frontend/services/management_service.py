from services.api_client import api_client


class ManagementService:
    def list(self, endpoint: str, query: str | None = None):
        return api_client.get(endpoint, params={"q": query} if query else None)

    def create(self, endpoint: str, payload: dict):
        return api_client.post(endpoint, payload)

    def update(self, endpoint: str, record_id, payload: dict):
        return api_client.put(f"{endpoint}/{record_id}", payload)


management_service = ManagementService()
