from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.services.llm_gateway import call_structured_json
from app.shared.state_types import AnalyserState


def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


CRITERION_HINTS = {
    "functional_requirements": "Add user stories with acceptance criteria and happy-path workflow.",
    "business_logic": "Document business rules, validations, and exception handling policies.",
    "existing_system": "Describe current architecture, integrations, and migration dependencies.",
    "target_audience": "List key personas, roles, and accessibility expectations.",
    "architecture_context": "Capture service boundaries, deployment environment, and security constraints.",
    "nfrs": "Specify performance, availability, scalability, and observability targets.",
    "timeline_budget": "Define milestones, phase-wise schedule, and budget estimates.",
    "visual_assets": "Include wireframes/mockups or describe major screens and UX flows.",
}


def enrich_node(state: AnalyserState) -> dict:
    """Add missing-context notes for low scoring criteria.

    We first create deterministic hints, then optionally let LLM refine them.
    """
    score = state.get("score")
    if score is None:
        return {}

    low_criteria = [
        criterion
        for criterion in CRITERION_HINTS
        if score.get(criterion, 0.0) < 0.67
    ]

    if not low_criteria:
        return {"needs_enrichment": False}

    enrichment_sections = []
    enrichment_text = []
    delta_changes = []

    for criterion in low_criteria:
        hint = CRITERION_HINTS[criterion]
        llm_hint = call_structured_json(
            prompt=(
                "Generate one concise enrichment hint for this criterion in plain English. "
                "Return JSON: {\"hint\": \"...\"}.\n"
                f"Criterion: {criterion}\n"
                f"Current score: {score.get(criterion, 0.0)}"
            ),
            fallback={"hint": hint},
        ).get("hint", hint)
        hint = str(llm_hint).strip() or hint
        enrichment_sections.append(
            {
                "file_name": "enrichment_notes.md",
                "section_heading": f"Enrichment - {criterion}",
                "page": None,
                "content_type": "text",
                "content": hint,
                "raw_image_ref": None,
            }
        )
        enrichment_text.append(f"- {criterion}: {hint}")
        delta_changes.append(
            {
                "change_id": str(uuid.uuid4()),
                "source": "enrichment",
                "source_ref": criterion,
                "field_path": "parsed_documents[]",
                "old_value": None,
                "new_value": hint,
                "timestamp": _now_iso(),
            }
        )

    enrichment_doc = {
        "file_name": "enrichment_notes.md",
        "file_type": "text/markdown",
        "s3_key": f"working/{state['project_id']}/enrichment_notes.md",
        "sections": enrichment_sections,
    }

    stream_event = {
        "event_id": str(uuid.uuid4()),
        "type": "enrichment_added",
        "node": "enrich_node",
        "payload": {
            "criteria": low_criteria,
            "note": "Synthetic enrichment generated from low-coverage criteria.",
            "summary": "\n".join(enrichment_text),
        },
        "timestamp": _now_iso(),
    }

    return {
        "parsed_documents": [enrichment_doc],
        "needs_enrichment": False,
        "delta_changes": delta_changes,
        "streaming_events": [stream_event],
    }
