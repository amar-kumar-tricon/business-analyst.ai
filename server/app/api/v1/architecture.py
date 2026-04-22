"""
app.api.v1.architecture
=======================
Stage 3 — Architecture agent endpoints.

BRD reference:
    §4.4 Architecture Agent
    §7.1 GET /architecture, POST /architecture/regenerate
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.architecture import ArchitectureOut

router = APIRouter(prefix="/projects/{project_id}/architecture", tags=["stage-3-architecture"])


@router.get("", response_model=ArchitectureOut)
async def get_architecture(project_id: str) -> ArchitectureOut:
    """Return Mermaid DSL strings and PlantUML-rendered SVGs for this project."""
    # TODO: read stage_outputs.stage='architecture' for latest version
    return ArchitectureOut(mermaid=[], plantuml=[])


@router.post("/regenerate")
async def regenerate(project_id: str) -> dict:
    """Re-run the Architecture agent with the same input — useful after edits."""
    # TODO: reset stage_outputs.architecture and re-invoke the graph node
    return {"project_id": project_id, "status": "regenerating"}
