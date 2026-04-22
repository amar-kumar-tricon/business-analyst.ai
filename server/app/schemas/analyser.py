"""Schemas for Stage 1 — Analyser agent output. Mirrors BRD §4.2."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProjectOverview(BaseModel):
    objective: str
    scope: str
    out_of_scope: str


class FunctionalRequirements(BaseModel):
    must_have: list[str] = Field(default_factory=list)
    should_have: list[str] = Field(default_factory=list)
    good_to_have: list[str] = Field(default_factory=list)


class Risk(BaseModel):
    title: str
    severity: Literal["low", "medium", "high"]
    description: str


class TeamRole(BaseModel):
    role: str
    count: int


class CompletenessScore(BaseModel):
    total: float = Field(ge=0, le=10)
    breakdown: dict[str, float] = Field(default_factory=dict)


class AnalyserResult(BaseModel):
    executive_summary: str
    project_overview: ProjectOverview
    functional_requirements: FunctionalRequirements
    risks: list[Risk] = Field(default_factory=list)
    recommended_team: list[TeamRole] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    completeness_score: CompletenessScore
    enriched: bool = False  # True if the agent had to synthesise missing context
