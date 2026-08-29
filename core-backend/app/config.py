from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "core-backend"
    debug: bool = False
    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"))

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"

    bootstrap_email: str = "admin@example.com"
    bootstrap_password: SecretStr = Field(default=SecretStr("changeme"))
    bootstrap_name: str = "Admin"

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    jwt_expiration_seconds: int = 60 * 60 * 24

    # Cursor SDK (course generation)
    cursor_api_key: SecretStr | None = None
    cursor_model: str = "composer-2.5"
    cursor_workspace: str = "/tmp/tin-yu-mal-cursor"

    # MinIO (S3-compatible uploads)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minio"
    minio_secret_key: SecretStr = Field(default=SecretStr("minio12345"))
    minio_bucket: str = "tin-yu-mal"
    minio_secure: bool = False
    upload_max_bytes: int = 10 * 1024 * 1024  # 10 MiB
    upload_context_max_chars: int = 12_000  # truncate text fed into LLM prompts


@lru_cache
def get_settings() -> Settings:
    return Settings()
