"""
app.api.v1.documents
====================
Multi-file upload endpoint. Saves files under `uploads/<project_id>/` via
`services.local_storage` and delegates parsing to `services.document_parser`.

BRD reference:
    §4.1 Document Upload & Input Panel
    §7.1 POST /api/projects/{project_id}/documents
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.config import settings
from app.services import local_storage

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["documents"])

ALLOWED_EXT = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    project_id: str,
    files: Annotated[list[UploadFile], File(...)],
    additional_context: Annotated[str, Form()] = "",
) -> dict:
    """Validate, save to local disk, and record metadata.

    TODO:
        1. insert a `documents` row per saved file (status='pending_parse')
        2. persist `additional_context` on the project row
        3. call `services.document_parser.parse()` synchronously (files are ≤ 50 MB)
    """
    saved: list[str] = []
    for f in files:
        filename = f.filename or "unnamed"
        ext = "." + filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(400, f"Unsupported file type: {filename}")
        if getattr(f, "size", 0) > settings.max_upload_bytes:
            raise HTTPException(413, f"File {filename} exceeds {settings.max_upload_mb} MB")

        local_storage.save_upload(project_id, filename, f.file)
        saved.append(filename)

    return {
        "project_id": project_id,
        "saved": saved,
        "context_len": len(additional_context),
    }
