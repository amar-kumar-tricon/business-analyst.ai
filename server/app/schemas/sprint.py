"""Schemas for Stage 4 — Sprint Planning agent. Mirrors BRD §4.5."""
from __future__ import annotations

from pydantic import BaseModel


class Story(BaseModel):
    id: str
    title: str
    points: int
    role: str
    acceptance: list[str] = []


class Sprint(BaseModel):
    number: int
    goal: str
    stories: list[Story] = []


class TeamRole(BaseModel):
    role: str
    count: int


class SprintPlanOut(BaseModel):
    total_sprints: int
    total_story_points: int
    total_man_hours: int
    mvp_cutoff_sprint: int
    sprints: list[Sprint] = []
    team_composition: list[TeamRole] = []
