from __future__ import annotations

import json
from typing import Any

from app.core.config import settings


STATE_DIR = settings.export_dir / "state_snapshots"
INDEX_DIR = settings.export_dir / "indexes"
ARTIFACT_DIR = settings.export_dir / "artifacts"


def _ensure_dirs() -> None:
    """Make sure export folders exist before writing files."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def save_state_snapshot(project_id: str, state: dict[str, Any]) -> str:
    """Save one project's current workflow state as JSON."""
    _ensure_dirs()
    path = STATE_DIR / f"{project_id}.json"
    path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return str(path.relative_to(settings.export_dir))


def load_state_snapshot(project_id: str) -> dict[str, Any] | None:
    """Load a saved state snapshot if it exists."""
    _ensure_dirs()
    path = STATE_DIR / f"{project_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_index(project_id: str, version: int, kind: str, records: list[dict[str, Any]]) -> str:
    """Save an index file (working or approved) for this project version."""
    _ensure_dirs()
    path = INDEX_DIR / f"{project_id}_v{version}_{kind}.json"
    payload = {"project_id": project_id, "version": version, "kind": kind, "records": records}
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(path.relative_to(settings.export_dir))


def save_artifact(project_id: str, version: int, extension: str, content: str | bytes) -> str:
    """Save an exported artifact and return a project-relative key/path."""
    _ensure_dirs()
    path = ARTIFACT_DIR / f"{project_id}_v{version}.{extension}"
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return str(path.relative_to(settings.export_dir))
