from __future__ import annotations

import json
import re
from pathlib import Path

from app.shared.state_types import ParsedSection


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_markdown(path: Path) -> list[ParsedSection]:
    text = _read_text(path)
    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
    matches = list(heading_re.finditer(text))

    if not matches:
        return [{
            "file_name": path.name,
            "section_heading": None,
            "page": None,
            "content_type": "text",
            "content": text.strip(),
            "raw_image_ref": None,
        }]

    sections: list[ParsedSection] = []

    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.append({
            "file_name": path.name,
            "section_heading": None,
            "page": None,
            "content_type": "text",
            "content": preamble,
            "raw_image_ref": None,
        })

    for i, m in enumerate(matches):
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        sections.append({
            "file_name": path.name,
            "section_heading": m.group(2).strip(),
            "page": None,
            "content_type": "text",
            "content": body,
            "raw_image_ref": None,
        })

    return sections


def _parse_plain_text(path: Path) -> list[ParsedSection]:
    return [{
        "file_name": path.name,
        "section_heading": None,
        "page": None,
        "content_type": "text",
        "content": _read_text(path).strip(),
        "raw_image_ref": None,
    }]


def _parse_csv(path: Path) -> list[ParsedSection]:
    return [{
        "file_name": path.name,
        "section_heading": None,
        "page": None,
        "content_type": "table",
        "content": _read_text(path).strip(),
        "raw_image_ref": None,
    }]


def _parse_json(path: Path) -> list[ParsedSection]:
    text = _read_text(path)
    try:
        pretty = json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        pretty = text
    return [{
        "file_name": path.name,
        "section_heading": None,
        "page": None,
        "content_type": "text",
        "content": pretty.strip(),
        "raw_image_ref": None,
    }]


_PARSERS = {
    ".md": _parse_markdown,
    ".markdown": _parse_markdown,
    ".txt": _parse_plain_text,
    ".csv": _parse_csv,
    ".json": _parse_json,
}


def parse_file(path: Path) -> list[ParsedSection]:
    """Parse a supported file and return normalized sections.

    Supported: .md/.markdown, .txt, .csv, .json.
    Unknown extensions fall back to plain-text best-effort.
    """
    parser = _PARSERS.get(path.suffix.lower(), _parse_plain_text)
    return parser(path)
