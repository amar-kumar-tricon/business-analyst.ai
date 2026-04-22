"""
app.agents.sprint.agent
=======================
STAGE 4 — Sprint Planning Agent.

Converts the finalised requirements + architecture into a sprint plan
(BRD §4.5). Output is a `SprintPlanOut` model.

Pipeline inside this agent:
    1. decompose features → epics → user stories
    2. estimate story points (reference velocity: 40 pts / 2-week sprint / dev)
    3. allocate stories to sprints (respect dependencies)
    4. identify MVP cut-off sprint
    5. recommend team composition
"""
from __future__ import annotations

from typing import Any

from app.agents.llm_factory import build_llm
from app.agents.sprint import prompts, tools  # noqa: F401
from app.agents.state import GraphState
from app.schemas.sprint import SprintPlanOut

AGENT_ID = "sprint"


async def sprint_node(state: GraphState) -> dict[str, Any]:
    llm = build_llm(AGENT_ID, state)  # noqa: F841

    # TODO:
    #   1. stories = tools.decompose(analyser_output, llm)
    #   2. pointed = tools.story_point(stories, llm)
    #   3. sprints = tools.allocate(pointed, velocity=40)
    #   4. mvp    = tools.mvp_cutoff(sprints, analyser_output.functional_requirements)
    #   5. team   = tools.size_team(sprints)

    plan = SprintPlanOut(
        total_sprints=0,
        total_story_points=0,
        total_man_hours=0,
        mvp_cutoff_sprint=0,
        sprints=[],
        team_composition=[],
    )
    return {"sprint_plan": plan, "current_stage": "sprint"}
