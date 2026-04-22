"""
app.services.local_storage
==========================
Saves / reads binary files on the local disk under `settings.upload_dir` and
`settings.export_dir`. Replaces what would otherwise be an S3/MinIO wrapper.

Layout on disk:
    uploads/<project_id>/<filename>
    exports/<project_id>/<stage>.<ext>

Keep all filesystem I/O behind this module so that swapping to cloud storage
later is a one-file change.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings


def _project_upload_dir(project_id: str) -> Path:
    path = settings.upload_dir / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _project_export_dir(project_id: str) -> Path:
    path = settings.export_dir / project_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(project_id: str, filename: str, fileobj: BinaryIO) -> Path:
    """Save an uploaded file to `uploads/<project_id>/<filename>` and return its path."""
    target = _project_upload_dir(project_id) / filename
    with target.open("wb") as out:
        shutil.copyfileobj(fileobj, out)
    return target


def read_upload(project_id: str, filename: str) -> bytes:
    return (_project_upload_dir(project_id) / filename).read_bytes()


def save_export(project_id: str, stage: str, ext: str, data: bytes) -> Path:
    target = _project_export_dir(project_id) / f"{stage}.{ext}"
    target.write_bytes(data)
    return target


def list_uploads(project_id: str) -> list[Path]:
    d = _project_upload_dir(project_id)
    return sorted(p for p in d.iterdir() if p.is_file())
