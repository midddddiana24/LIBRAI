from services.api_client import ApiResult, api_client


class AuthService:
    def login(self, username: str, password: str) -> ApiResult:
        result = api_client.post("/auth/login", {"username": username, "password": password})
        if result.ok:
            api_client.set_auth_token(result.data.get("access_token"))
        return result

    def restore_token(self, token: str | None) -> None:
        api_client.set_auth_token(token)

    def current_admin(self) -> ApiResult:
        """Validate a restored session and return its current administrator."""
        return api_client.get("/auth/me")

    def logout(self) -> ApiResult:
        result = api_client.post("/auth/logout")
        api_client.set_auth_token(None)
        return result


auth_service = AuthService()
