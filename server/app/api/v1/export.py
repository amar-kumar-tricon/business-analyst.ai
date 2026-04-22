"""
app.api.v1.export
=================
Export any stage output as PDF or DOCX.

BRD reference:
    §1.1 Export capability
    §7.1 POST /projects/{project_id}/export
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.schemas.project import ExportRequest

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])


@router.post("")
async def export_stage(project_id: str, payload: ExportRequest) -> Response:
    """Render the given stage's output into PDF (WeasyPrint) or DOCX (python-docx).

    TODO:
        * load stage output JSON
        * delegate to `services.export_service.to_pdf` / `.to_docx`
        * return as `Response(content=bytes, media_type=..., headers={Content-Disposition})`
    """
    content = b"PDF-PLACEHOLDER"
    media = "application/pdf" if payload.format == "pdf" else (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    filename = f"{project_id}-{payload.stage}.{payload.format}"
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
