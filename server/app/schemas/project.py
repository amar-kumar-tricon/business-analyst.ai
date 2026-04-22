"""Pydantic schemas for the `projects` resource."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

StageName = Literal["upload", "analyse", "discovery", "architecture", "sprint", "finalized"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ProjectOut(BaseModel):
    id: str
    name: str
    current_stage: StageName
    version: int
    created_at: str


class ApprovalRequest(BaseModel):
    edits: Any | None = None  # free-form edits blob applied before approval


class ExportRequest(BaseModel):
    stage: StageName
    format: Literal["pdf", "docx"]
