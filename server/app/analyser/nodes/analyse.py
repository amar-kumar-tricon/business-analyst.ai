from __future__ import annotations

from app.shared.state_types import AnalyserState


def analyse_node(state: AnalyserState) -> dict:
    # Deterministic placeholder output so upstream/downstream wiring can be tested.
    score = state["score"]
    analyser_output = {
        "executive_summary": "Placeholder analysis summary.",
        "project_overview": {
            "objective": "TBD",
            "scope": "TBD",
            "out_of_scope": "TBD",
        },
        "functional_requirements": [],
        "risks": [],
        "recommended_team": {
            "roles": [],
            "size": 0,
            "rationale": "TBD",
        },
        "open_questions": [],
        "completeness_score": score,
        "assumptions_made": [],
    }

    return {"analyser_output": analyser_output}
