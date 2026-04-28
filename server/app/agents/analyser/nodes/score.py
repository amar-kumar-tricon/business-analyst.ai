from __future__ import annotations

from app.shared.state_types import AnalyserState


CRITERION_NAMES = [
    "functional_requirements",
    "business_logic",
    "existing_system",
    "target_audience",
    "architecture_context",
    "nfrs",
    "timeline_budget",
    "visual_assets",
]


def score_node(state: AnalyserState) -> dict:
    # Placeholder scoring to keep graph flow testable before LLM integration.
    score = {
        "functional_requirements": 0.5,
        "business_logic": 0.5,
        "existing_system": 0.5,
        "target_audience": 0.5,
        "architecture_context": 0.5,
        "nfrs": 0.5,
        "timeline_budget": 0.5,
        "visual_assets": 0.5,
        "weighted_total": 5.0,
        "per_criterion_reasoning": {
            name: "Placeholder reasoning: criterion parser not implemented yet."
            for name in CRITERION_NAMES
        },
    }

    return {
        "score": score,
        "needs_enrichment": score["weighted_total"] <= 5.0,
    }
