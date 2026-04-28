from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_debug: bool = True
    app_cors_origins: str = "http://localhost:5173"

    database_url: str = "sqlite:///./bra_tool.db"
    database_url_sync: str = "sqlite:///./bra_tool.db"

    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str = "us-east-1"
    s3_bucket_uploads: str = "bra-uploads"
    s3_bucket_exports: str = "bra-exports"

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    default_model_provider: str = "openai"
    default_model_name: str = "gpt-4o-mini"

    upload_dir: Path = Path("./uploads")
    export_dir: Path = Path("./exports")

    max_upload_mb: int = 50

    @field_validator("upload_dir", "export_dir", mode="before")
    @classmethod
    def _resolve_paths(cls, value: str | Path) -> Path:
        path_value = Path(value)
        if path_value.is_absolute():
            return path_value

        server_root = Path(__file__).resolve().parents[2]
        return (server_root / path_value).resolve()

    @property
    def cors_origins_list(self) -> list[str]:
        """Split comma-separated CORS origins into a clean list."""
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]


settings = Settings()
