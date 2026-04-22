"""
app.api.v1.versions
===================
Finalize a project (create an immutable v_N snapshot) and list versions.

BRD reference:
    §10 Versioning & Change Management
    §7.1 POST /finalize, GET /versions
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/projects/{project_id}", tags=["versions"])


@router.post("/finalize")
async def finalize(project_id: str) -> dict:
    """Create an immutable snapshot of every stage output.

    TODO:
        * gather all stage_outputs rows for current version
        * serialise into JSON and insert into `project_versions`
        * bump projects.version and set status='finalized'
    """
    return {"project_id": project_id, "new_version": 1}


@router.get("/versions")
async def list_versions(project_id: str) -> list[dict]:
    """List every snapshot ever created for this project."""
    # TODO: SELECT * FROM project_versions WHERE project_id = ? ORDER BY version_number
    return []
