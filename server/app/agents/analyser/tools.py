"""
app.agents.analyser.tools
=========================
Discrete, unit-testable tools used by the Analyser agent.

Each tool is a plain (async) function so juniors can write tests against them
without spinning up an LLM. Expose them to the LLM via `@tool` decorator if you
want the model to call them directly.
"""
from __future__ import annotations

from typing import Any


# Criterion → weight, mirroring BRD §4.2 scoring rubric.
SCORING_WEIGHTS: dict[str, float] = {
    "functional_requirements": 0.20,
    "business_logic": 0.15,
    "existing_system_info": 0.15,
    "target_audience": 0.10,
    "architecture_context": 0.15,
    "non_functional_requirements": 0.10,
    "timeline_budget": 0.10,
    "visual_assets": 0.05,
}


def score_document(text: str) -> tuple[float, dict[str, float]]:
    """Return a (total_score_0_to_10, per_criterion_breakdown) tuple.

    TODO:
        * replace this heuristic with an LLM call that scores each criterion
        * keep the return shape stable — downstream code depends on it.
    """
    # Dumb baseline: longer docs score higher. Replace ASAP.
    per_c = {k: min(10.0, len(text) / 2000) for k in SCORING_WEIGHTS}
    total = sum(per_c[k] * w for k, w in SCORING_WEIGHTS.items())
    return round(total, 2), per_c


async def enrich(text: str, llm: Any) -> str:
    """Ask the LLM to fill missing context. Called only when score < 6."""
    # TODO: prompt = prompts.ENRICHMENT + text; return (await llm.ainvoke(prompt)).content
    return text


def classify_moscow(requirements: list[str]) -> dict[str, list[str]]:
    """Bucket requirements into Must/Should/Good.

    TODO: use an LLM with few-shot examples; keep prompts in prompts.py.
    """
    return {"must_have": [], "should_have": [], "good_to_have": []}


def extract_risks(text: str) -> list[dict]:
    """Return a list of {title, severity, description} dicts."""
    # TODO: LLM + validation
    return []


def recommend_team(text: str) -> list[dict]:
    """Return a list of {role, count} dicts based on the requirement shape."""
    return []
