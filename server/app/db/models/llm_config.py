"""ORM model for `llm_configs`. BRD §8.1."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LLMConfigRow(Base):
    __tablename__ = "llm_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # analyser/discovery/...
    provider: Mapped[str] = mapped_column(String(32))  # openai/anthropic/...
    model_name: Mapped[str] = mapped_column(String(64))
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    api_key_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)  # e.g. "OPENAI_API_KEY"
