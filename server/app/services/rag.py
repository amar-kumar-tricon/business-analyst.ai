from __future__ import annotations

from hashlib import sha1


def build_chunk_id(project_id: str, text: str) -> str:
    """Create a stable chunk id from project id and text."""
    return sha1(f"{project_id}:{text}".encode("utf-8")).hexdigest()[:16]


def build_working_records(project_id: str, parsed_documents: list[dict]) -> tuple[list[str], list[dict]]:
    """Create lightweight working RAG records from parsed document sections."""
    chunk_ids: list[str] = []
    records: list[dict] = []

    for doc in parsed_documents:
        for section in doc.get("sections", []):
            text = section.get("content", "")
            chunk_id = build_chunk_id(project_id, text)
            chunk_ids.append(chunk_id)
            records.append(
                {
                    "chunk_id": chunk_id,
                    "file_name": doc.get("file_name"),
                    "section_heading": section.get("section_heading") or "Untitled",
                    "content_preview": text[:160],
                }
            )

    return chunk_ids, records
