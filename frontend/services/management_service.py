from services.api_client import api_client


class ManagementService:
    def list(self, endpoint: str, query: str | None = None, offset: int = 0, limit: int = 25):
        params = {"offset": offset, "limit": limit}
        if query:
            params["q"] = query
        return api_client.get(endpoint, params=params)

    def create(self, endpoint: str, payload: dict):
        return api_client.post(endpoint, payload)

    def update(self, endpoint: str, record_id, payload: dict):
        return api_client.put(f"{endpoint}/{record_id}", payload)


management_service = ManagementService()
