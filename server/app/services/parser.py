from __future__ import annotations

from pathlib import Path


def parse_text_file(path: Path) -> list[dict]:
    """Parse a plain text file into one section so the graph can consume it."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    return [
        {
            "file_name": path.name,
            "section_heading": "Imported Text",
            "page": 1,
            "content_type": "text",
            "content": content,
            "raw_image_ref": None,
        }
    ]


def parse_file(path: Path) -> list[dict]:
    """Parse a supported file and return normalized sections.

    For now, we support text/markdown/csv/json as text blocks.
    """
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv", ".json"}:
        return parse_text_file(path)

    # Fallback: treat unknown formats as text best-effort.
    return parse_text_file(path)
