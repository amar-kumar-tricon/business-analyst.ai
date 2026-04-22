"""
app.core.config
===============
Typed settings loaded from environment / `.env` via pydantic-settings.

Access pattern from anywhere in the codebase:
    >>> from app.core.config import settings
    >>> settings.database_url

Adding a new env var:
    1. Add a typed field below (with a sensible default where possible).
    2. Document it in `server/.env.example`.
    3. Reference it via `settings.<field>` — never call `os.getenv` directly.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- App ----
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_cors_origins: str = "http://localhost:5173"

    # ---- Database ----
    database_url: str = "sqlite:///./bra_tool.db"

    # ---- Local file storage ----
    upload_dir: Path = Path("./uploads")
    export_dir: Path = Path("./exports")

    # ---- LLM providers ----
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    llm_analyser_model: str = "gpt-4o"
    llm_discovery_model: str = "gpt-4o"
    llm_architecture_model: str = "gpt-4o"
    llm_sprint_model: str = "gpt-4o"

    # ---- Observability ----
    langsmith_api_key: str | None = None
    langsmith_project: str = "bra-tool"

    # ---- Uploads ----
    max_upload_mb: int = Field(default=50, ge=1, le=500)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def _load() -> Settings:
    return Settings()


settings = _load()
