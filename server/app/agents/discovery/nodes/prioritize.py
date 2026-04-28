from __future__ import annotations

from copy import deepcopy

from app.shared.state_types import DiscoveryState


def prioritize_questions_node(state: DiscoveryState) -> dict:
    """Sort open questions by downstream impact.

    Placeholder: returns questions exactly as-is.
    Real impl will: call LLM to rank by 'most blocking decisions first',
    verify all original question_ids are still present, then update
    state["analyser_output"]["open_questions"] with priority field set.
    """
    open_questions = state["analyser_output"].get("open_questions", [])

    if not open_questions:
        # Nothing to prioritize — proceed to generate_question_node
        # which will terminate immediately.
        return {}

    # Placeholder: mark every question as medium priority until LLM is wired.
    updated = deepcopy(state["analyser_output"])
    for q in updated["open_questions"]:
        if "priority" not in q:
            q["priority"] = "medium"

    return {"analyser_output": updated}
