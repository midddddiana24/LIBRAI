from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LIBRAI API"
    environment: str = "development"
    database_url: str = "sqlite:///./librai.db"
    secret_key: str = "development-only-change-this-secret-key"
    access_token_expire_minutes: int = 60
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    cors_origins: list[str] | str = ["http://127.0.0.1:8550", "http://localhost:8550"]
    report_directory: Path = Path("generated/reports")
    max_upload_bytes: int = 5 * 1024 * 1024
    default_borrowing_limit: int = 3
    default_borrowing_period_days: int = 7
    default_allow_borrow_with_overdue: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False, extra="ignore")

    @field_validator("environment", mode="before")
    @classmethod
    def alias_environment(cls, value):
        return value or "development"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def protect_production_secret(self):
        if self.environment.lower() == "production" and (self.secret_key == "development-only-change-this-secret-key" or len(self.secret_key) < 32):
            raise ValueError("Production SECRET_KEY must be a unique value of at least 32 characters.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings(
        environment=__import__("os").getenv("LIBRAI_ENV", "development")
    )


settings = get_settings()
