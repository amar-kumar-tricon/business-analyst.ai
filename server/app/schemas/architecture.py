"""Schemas for Stage 3 — Architecture agent."""
from __future__ import annotations

from pydantic import BaseModel


class MermaidDiagram(BaseModel):
    id: str
    title: str
    dsl: str


class PlantUMLDiagram(BaseModel):
    id: str
    title: str
    dsl: str
    svg: str | None = None  # rendered server-side


class ArchitectureOut(BaseModel):
    mermaid: list[MermaidDiagram] = []
    plantuml: list[PlantUMLDiagram] = []
