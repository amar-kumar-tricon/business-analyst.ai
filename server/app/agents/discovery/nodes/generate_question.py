from __future__ import annotations

from app.shared.state_types import DiscoveryState, QAExchange
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_question_node(state: DiscoveryState) -> dict:
    """Pick the next most-impactful unanswered question.

    Placeholder: picks the first unanswered open question from
    analyser_output.open_questions. Returns current_question=None
    when nothing is left (which causes _route_after_process to finalize).

    Real impl will:
    - Retrieve relevant chunks from RAG for grounding.
    - Ask LLM to select the single highest-impact question with
      rationale and 2-4 concrete answer options.
    - Handle LLM 'terminate' signal (no high-value questions left).
    """
    # Hard cap guard
    if state["questions_asked_count"] >= 10:
        return {"current_question": None}

    already_asked = {qa["question_id"] for qa in state["qa_history"]}
    unanswered = [
        q for q in state["analyser_output"].get("open_questions", [])
        if q["question_id"] not in already_asked
    ]

    if not unanswered:
        # Nothing left to ask — signal termination
        return {"current_question": None}

    next_q = unanswered[0]

    # Build a minimal QAExchange (answer/status filled in on resume)
    current_question: QAExchange = {
        "question_id": next_q["question_id"],
        "question": next_q["question"],
        "rationale": "Placeholder rationale — LLM not yet wired.",
        "options": ["Option A", "Option B"],
        "answer": None,
        "selected_option_index": None,
        "status": "answered",       # will be overwritten by resume payload
        "timestamp": _now_iso(),
        "triggered_changes": [],
    }

    return {
        "current_question": current_question,
        "questions_asked_count": state["questions_asked_count"] + 1,
    }
