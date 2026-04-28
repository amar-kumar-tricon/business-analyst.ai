from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timezone

from app.shared.state_types import DeltaChange, DiscoveryState


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def process_answer_node(state: DiscoveryState) -> dict:
    """Apply the user's answer to analyser_output and record audit trail.

    Placeholder: stores the answer in qa_history and clears current_question
    without mutating analyser_output (no LLM-generated patches yet).

    Real impl will:
    - If status == 'answered': ask LLM for RFC 6902 JSON patches, apply
      them deterministically with the jsonpatch library, log DeltaChange
      per patch.
    - If status == 'deferred': tag the open question priority='low'.
    - If status == 'na': remove the question from open_questions entirely.
    - If status == 'unknown': leave in open_questions for analytics.
    """
    qa = state.get("current_question")
    if qa is None:
        # Defensive: nothing to process.
        return {}

    new_analyser = deepcopy(state["analyser_output"])
    new_deltas: list[DeltaChange] = []

    status = qa.get("status", "answered")

    if status == "deferred":
        for q in new_analyser["open_questions"]:
            if q["question_id"] == qa["question_id"]:
                q["priority"] = "low"
                break

    elif status == "na":
        new_analyser["open_questions"] = [
            q for q in new_analyser["open_questions"]
            if q["question_id"] != qa["question_id"]
        ]

    # Placeholder delta (no real patch yet)
    new_deltas.append(DeltaChange(
        change_id=str(uuid.uuid4()),
        source="qa",
        source_ref=qa["question_id"],
        field_path="(placeholder — no patch applied yet)",
        old_value=None,
        new_value=str(qa.get("answer", "")),
        timestamp=_now_iso(),
    ))

    qa["triggered_changes"] = []

    return {
        "analyser_output": new_analyser,
        "qa_history": [qa],          # appended via Annotated[list, add] reducer
        "current_question": None,    # clear after processing
        "delta_changes": new_deltas, # appended via reducer
    }
