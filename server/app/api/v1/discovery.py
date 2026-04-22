"""
app.api.v1.discovery
====================
Stage 2 — Discovery / QnA agent.

BRD reference:
    §4.3 Discovery / QnA Agent
    §7.1 GET /discovery, POST /discovery/answer
"""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.discovery import DiscoveryAnswerIn, DiscoveryState

router = APIRouter(prefix="/projects/{project_id}/discovery", tags=["stage-2-discovery"])


@router.get("", response_model=DiscoveryState)
async def get_discovery(project_id: str) -> DiscoveryState:
    """Return the current question plus the full Q&A history.

    TODO:
        * read `discovery_qa` rows for this project
        * call discovery agent's `next_question()` if all pending are answered
    """
    return DiscoveryState(project_id=project_id, current_question=None, history=[])


@router.post("/answer")
async def submit_answer(project_id: str, payload: DiscoveryAnswerIn) -> dict:
    """Record an answer / deferral / N-A and trigger a delta update to the Analyser output.

    TODO:
        * persist the QA row
        * call AnswerProcessorTool → StateUpdaterTool to patch analyser_output
        * return the delta diff so the UI can highlight changes
    """
    return {"project_id": project_id, "status": payload.status}
