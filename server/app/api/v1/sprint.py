"""
app.api.v1.sprint
=================
Stage 4 — Sprint Planning agent endpoints.

BRD reference:
    §4.5 Sprint Planning Agent
    §7.1 GET /sprint
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.sprint import SprintPlanOut

router = APIRouter(prefix="/projects/{project_id}/sprint", tags=["stage-4-sprint"])


@router.get("", response_model=SprintPlanOut)
async def get_sprint(project_id: str) -> SprintPlanOut:
    """Return the generated sprint plan.

    TODO:
        * read stage_outputs.stage='sprint' for latest version
        * return an empty plan if not yet generated
    """
    return SprintPlanOut(
        total_sprints=0,
        total_story_points=0,
        total_man_hours=0,
        mvp_cutoff_sprint=0,
        sprints=[],
        team_composition=[],
    )
