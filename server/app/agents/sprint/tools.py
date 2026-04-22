"""
app.agents.sprint.tools
=======================
Decomposition / estimation / allocation helpers for the Sprint Planning agent.
"""
from __future__ import annotations

from typing import Any


async def decompose(analyser_output: Any, llm: Any) -> list[dict]:
    """Break each functional requirement into discrete user stories."""
    # TODO: LLM call — return list of {title, description, role_hint}
    return []


async def story_point(stories: list[dict], llm: Any) -> list[dict]:
    """Attach a fibonacci point value to each story. Use 1,2,3,5,8,13 only."""
    return stories


def allocate(stories: list[dict], *, velocity: int = 40) -> list[dict]:
    """Greedy allocation: fill each sprint until capacity is hit, then open the next."""
    sprints: list[dict] = []
    current: dict = {"number": 1, "goal": "", "stories": [], "capacity": velocity}
    for s in stories:
        pts = s.get("points", 0)
        if pts > current["capacity"]:
            sprints.append(current)
            current = {"number": current["number"] + 1, "goal": "", "stories": [], "capacity": velocity}
        current["stories"].append(s)
        current["capacity"] -= pts
    if current["stories"]:
        sprints.append(current)
    return sprints


def mvp_cutoff(sprints: list[dict], requirements: dict) -> int:
    """Return the sprint number where all Must-Have stories are delivered."""
    # TODO: inspect which stories map to must_have requirements
    return len(sprints) // 2 if sprints else 0


def size_team(sprints: list[dict]) -> list[dict]:
    """Recommend a team composition based on role coverage across sprints."""
    return [
        {"role": "Frontend Dev", "count": 2},
        {"role": "Backend Dev", "count": 2},
        {"role": "QA", "count": 1},
        {"role": "DevOps", "count": 1},
        {"role": "PM", "count": 1},
    ]
