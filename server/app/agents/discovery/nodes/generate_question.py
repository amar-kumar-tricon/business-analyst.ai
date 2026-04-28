from __future__ import annotations

from datetime import datetime, timezone

from app.services.llm_gateway import call_structured_json
from app.shared.state_types import DiscoveryState, QAExchange


def _now_iso() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def generate_question_node(state: DiscoveryState) -> dict:
    """Pick one unanswered question and build answer options for the user."""
    if state["questions_asked_count"] >= 10:
        return {"current_question": None}

    already_asked = {qa["question_id"] for qa in state["qa_history"]}
    unanswered = [
        q for q in state["analyser_output"].get("open_questions", [])
        if q["question_id"] not in already_asked
    ]

    if not unanswered:
        return {"current_question": None}

    next_q = unanswered[0]
    blocked = next_q.get("blocked_decisions", [])
    options = [
        "Proceed with current baseline assumptions",
        "Refine details before approval",
    ]
    if blocked:
        options.append(f"Prioritize resolution of: {blocked[0]}")

    llm_payload = call_structured_json(
        prompt=(
            "Create concise rationale and 2-4 options for this question. "
            "Return JSON {\"rationale\":\"...\",\"options\":[...]}.\n"
            f"Question: {next_q['question']}"
        ),
        fallback={
            "rationale": "Chosen because it blocks high-impact decisions and is still unanswered.",
            "options": options,
        },
    )
    llm_rationale = str(llm_payload.get("rationale", "")).strip()
    llm_options = llm_payload.get("options", options)
    if isinstance(llm_options, list) and llm_options:
        options = [str(o) for o in llm_options[:4]]

    current_question: QAExchange = {
        "question_id": next_q["question_id"],
        "question": next_q["question"],
        "rationale": llm_rationale or (
            "Chosen because it blocks high-impact decisions and has not yet "
            "been answered in this discovery run."
        ),
        "options": options,
        "answer": None,
        "selected_option_index": None,
        "status": "answered",
        "timestamp": _now_iso(),
        "triggered_changes": [],
    }

    return {
        "current_question": current_question,
        "questions_asked_count": state["questions_asked_count"] + 1,
    }
