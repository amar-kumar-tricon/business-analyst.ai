"""
app.agents.discovery.tools
==========================
Tools for the Discovery agent: question generation, answer processing, and
state-updating patches to analyser_output.
"""
from __future__ import annotations

from typing import Any


async def generate_next_question(open_qs: list[str], history: list[dict], analyser_output: Any, llm: Any) -> str | None:
    """Return the next question text, or None when nothing valuable remains."""
    # TODO: prompt the LLM; respect the "<DONE>" sentinel.
    return open_qs[0] if open_qs else None


async def process_answer(question: str, answer: str, analyser_output: Any, llm: Any) -> dict:
    """Return a JSON patch to apply to analyser_output based on the answer."""
    # TODO: LLM call; validate patch shape.
    return {}


def apply_patch(analyser_output: dict, patch: dict) -> dict:
    """Merge `patch` into `analyser_output` — used by StateUpdaterTool."""
    merged = {**analyser_output, **patch}
    return merged
