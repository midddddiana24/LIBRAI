from services.api_client import api_client


class AdminService:
    def dashboard(self):
        return api_client.get("/admin/dashboard")

    def report_list(self, **params):
        return api_client.get("/reports", params=params)

    def export_report(self, payload):
        result = api_client.post("/reports/export", payload)
        if result.ok and isinstance(result.data, dict) and result.data.get("download_url"):
            result.data["download_url"] = api_client.resolve_url(result.data["download_url"])
        return result

    def audit_logs(self, **params):
        return api_client.get("/audit-logs", params=params)

    def settings(self):
        return api_client.get("/settings")

    def update_setting(self, key: str, value):
        return api_client.put(f"/settings/{key}", {"value": value})

    def update_settings(self, values: dict):
        return api_client.put("/settings", values)


admin_service = AdminService()
