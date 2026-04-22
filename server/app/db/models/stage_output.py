"""ORM model for `stage_outputs` table. BRD §8.1."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StageOutput(Base):
    __tablename__ = "stage_outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    version: Mapped[int] = mapped_column(default=1)
    stage: Mapped[str] = mapped_column(String(32))  # analyse/discovery/architecture/sprint
    output_json: Mapped[dict] = mapped_column(JSON)
    edits_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
