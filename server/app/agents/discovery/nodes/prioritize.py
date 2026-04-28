from __future__ import annotations

from copy import deepcopy

from app.services.llm_gateway import call_structured_json
from app.shared.state_types import DiscoveryState


PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _rank_question(question: dict) -> tuple[int, int, str]:
    """Deterministic sorting key for open questions."""
    priority = question.get("priority", "medium")
    blocked_count = len(question.get("blocked_decisions", []))
    return (PRIORITY_ORDER.get(priority, 1), -blocked_count, question.get("question_id", ""))


def prioritize_questions_node(state: DiscoveryState) -> dict:
    """Sort open questions by priority.

    We first do deterministic sorting, then ask LLM for optional re-ordering.
    """
    open_questions = state["analyser_output"].get("open_questions", [])

    if not open_questions:
        return {}

    updated = deepcopy(state["analyser_output"])
    for q in updated["open_questions"]:
        if "priority" not in q:
            q["priority"] = "medium"

    updated["open_questions"] = sorted(updated["open_questions"], key=_rank_question)

    # Optional LLM ranking by question_id order.
    ranked_ids = call_structured_json(
        prompt=(
            "Rank these questions by business impact. Return JSON {\"order\": [question_id,...]} only.\n"
            f"Questions: {updated['open_questions']}"
        ),
        fallback={"order": [q["question_id"] for q in updated["open_questions"]]},
    ).get("order", [])

    if ranked_ids:
        rank_map = {qid: idx for idx, qid in enumerate(ranked_ids)}
        updated["open_questions"] = sorted(
            updated["open_questions"],
            key=lambda q: (rank_map.get(q.get("question_id", ""), 999), _rank_question(q)),
        )

    return {"analyser_output": updated}
