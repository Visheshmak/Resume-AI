from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ResumeIQ API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://resumeiq:resumeiq@localhost:5432/resumeiq"
    jwt_secret_key: str = Field(default="replace-me-with-a-random-32-byte-key", min_length=32)
    cors_origins: list[str] = ["http://localhost:5173"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver", "test"]
    llm_provider: str = "stub"
    llm_api_key: str | None = None
    embedding_provider: str = "stub"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 20.0
    openai_base_url: str = "https://api.openai.com/v1"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    upload_dir: str = "data/uploads"
    max_upload_size_bytes: int = 5 * 1024 * 1024
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    vector_database_url: str | None = None
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    redis_url: str | None = None
    analysis_max_retries: int = 3
    analysis_version: str = "v1.0"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env.lower() in {"production", "staging"} and self.jwt_secret_key.startswith("replace-me"):
            raise ValueError("JWT_SECRET_KEY must be set to a unique secret outside development")
        return self

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
