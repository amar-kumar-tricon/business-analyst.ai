"""
app.api.v1.projects
===================
Project lifecycle endpoints.

BRD reference:  §7.1  POST /projects, GET /projects/{id}, POST /approve/{stage}

Guideline for juniors:
    * Keep route functions THIN — parse the request, delegate to a service/agent,
      shape the response. No SQL, no LangGraph calls directly here.
"""
from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.schemas.project import (
    ApprovalRequest,
    ProjectCreate,
    ProjectOut,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate) -> ProjectOut:
    """Create a new project session.

    TODO:
        * persist a `projects` row (status='draft', current_stage='upload', version=1)
        * return the ORM row mapped through ProjectOut
    """
    # PLACEHOLDER — replace with actual DB insert via a ProjectService.
    return ProjectOut(
        id=str(uuid4()),
        name=payload.name,
        current_stage="upload",
        version=1,
        created_at="1970-01-01T00:00:00Z",
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str) -> ProjectOut:
    """Fetch a project with every stage output merged in.

    TODO:
        * JOIN projects + stage_outputs (latest version)
        * include discovery_qa list and open_questions in the response
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/{project_id}/approve/{stage}")
async def approve_stage(project_id: str, stage: str, payload: ApprovalRequest) -> dict:
    """Human approval gate — advances the LangGraph past the `human_review_N` interrupt.

    TODO:
        * persist approval + any inline edits to `stage_outputs.edits_json`
        * call `app.agents.graph.resume(project_id)` so LangGraph continues
    """
    return {"project_id": project_id, "stage": stage, "approved": True, "edits": payload.edits}
