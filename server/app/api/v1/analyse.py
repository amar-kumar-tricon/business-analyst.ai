"""
app.api.v1.analyse
==================
Triggers Stage 1 — the Document Analyser agent.

BRD reference:
    §4.2 Stage 1 — Document Analyser Agent
    §7.1 POST /api/projects/{project_id}/analyse
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, status

router = APIRouter(prefix="/projects/{project_id}/analyse", tags=["stage-1-analyser"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def trigger_analyser(project_id: str, background: BackgroundTasks) -> dict:
    """Kick off the Analyser agent asynchronously.

    TODO:
        * load the project's uploaded_documents + additional_context
        * hydrate a GraphState and call `app.agents.graph.invoke(state)` in background
        * stream tokens over `/ws/projects/{id}/stream`
    """
    # background.add_task(run_analyser_pipeline, project_id)
    return {"project_id": project_id, "status": "analyser_started"}
