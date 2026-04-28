from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timezone

from app.services.llm_gateway import call_structured_json
from app.shared.state_types import DeltaChange, DiscoveryState


def _now_iso() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def process_answer_node(state: DiscoveryState) -> dict:
    """Apply one user answer into analyser output and log change history."""
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

    elif status == "answered":
        answer = (qa.get("answer") or "").strip()
        if answer:
            # Step 1: keep deterministic requirement append so output is never empty.
            req_id = f"FR-QA-{len(new_analyser['functional_requirements']) + 1:03d}"
            new_analyser["functional_requirements"].append(
                {
                    "req_id": req_id,
                    "description": f"Decision from {qa['question_id']}: {answer}",
                    "moscow": "should_have",
                    "acceptance_hints": ["Validated by stakeholder answer during discovery."],
                    "source": "qa",
                    "source_ref": qa["question_id"],
                }
            )

            # Step 2: optional LLM JSON Patch for richer updates.
            patch_payload = call_structured_json(
                prompt=(
                    "Create RFC6902 patch list for analyser_output based on this answered question. "
                    "Return JSON {\"patches\": [...]} only.\n"
                    f"Question: {qa['question']}\nAnswer: {answer}\n"
                    f"Current analyser_output: {new_analyser}"
                ),
                fallback={"patches": []},
            )
            patches = patch_payload.get("patches", [])
            if isinstance(patches, list) and patches:
                try:
                    import jsonpatch

                    patched = jsonpatch.apply_patch(deepcopy(new_analyser), patches, in_place=False)
                    if isinstance(patched, dict):
                        new_analyser = patched
                except Exception:
                    # Ignore patch errors and keep deterministic data.
                    pass

    new_deltas.append(DeltaChange(
        change_id=str(uuid.uuid4()),
        source="qa",
        source_ref=qa["question_id"],
        field_path="analyser_output.functional_requirements",
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
