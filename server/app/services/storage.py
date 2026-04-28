from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def upload_local_file(file_path: Path, object_key: str) -> str:
    """Save file to local uploads area and return storage key.

    In local learning mode this behaves like object storage.
    """
    target = settings.upload_dir / object_key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(file_path.read_bytes())
    return str(target.relative_to(settings.upload_dir))


def save_export_bytes(content: bytes, object_key: str) -> str:
    """Save exported binary content under exports folder."""
    target = settings.export_dir / object_key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return str(target.relative_to(settings.export_dir))
