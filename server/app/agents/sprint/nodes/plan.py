from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.services.llm_gateway import call_structured_json
from app.shared.state_types import SprintPlan


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SPRINT_DURATION_WEEKS = 2
_TOTAL_SPRINTS = 6
_MVP_CUTOFF_SPRINT = 4


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Internal Tools
# ---------------------------------------------------------------------------

def StoryDecomposerTool(functional_requirements: list[dict]) -> list[dict]:
    """Break each functional requirement into a raw user story dict."""
    stories: list[dict] = []
    for idx, fr in enumerate(functional_requirements):
        stories.append(
            {
                "story_id": f"RAW-{idx + 1:03d}",
                "title": fr.get("description", f"Story {idx + 1}")[:80],
                "description": (
                    f"As a user, I want to {fr.get('description', 'complete this requirement').lower()}"
                ),
                "acceptance_criteria": fr.get("acceptance_hints", ["Functional and tested end-to-end."]),
                "moscow": fr.get("moscow", "should_have"),
                "req_id": fr.get("req_id", f"FR-{idx + 1:03d}"),
            }
        )
    return stories


def StoryPointerTool(raw_stories: list[dict]) -> list[dict]:
    """Assign story points to each raw story based on MoSCoW priority."""
    pointed: list[dict] = []
    for story in raw_stories:
        moscow = story.get("moscow", "should_have")
        if moscow == "must_have":
            points = 5
        elif moscow == "should_have":
            points = 3
        else:
            points = 2
        pointed.append({**story, "story_points": points})
    return pointed


def MVPClassifierTool(pointed_stories: list[dict], mvp_cutoff_sprint: int) -> list[dict]:
    """Tag each story as MVP or post-MVP based on MoSCoW priority."""
    classified: list[dict] = []
    for story in pointed_stories:
        is_mvp = story.get("moscow") in {"must_have", "should_have"}
        classified.append({**story, "is_mvp": is_mvp})
    return classified


def TeamSizerTool(recommended_team: dict) -> list[dict]:
    """
    Derive team composition from recommended_team.
    Falls back to the spec default (FE Dev x2, BE Dev x2, QA x1, DevOps x1, PM x1)
    when recommended_team doesn't contain enough role detail.
    """
    roles = recommended_team.get("roles", [])
    generic = {"Business Analyst", "Tech Lead", "QA Engineer"}
    if not roles or set(roles) == generic or len(roles) < 4:
        return [
            {"role": "FE Dev",  "count": 2, "hours_per_sprint": 80},
            {"role": "BE Dev",  "count": 2, "hours_per_sprint": 80},
            {"role": "QA",      "count": 1, "hours_per_sprint": 40},
            {"role": "DevOps",  "count": 1, "hours_per_sprint": 40},
            {"role": "PM",      "count": 1, "hours_per_sprint": 20},
        ]
    hour_map = {"FE Dev": 80, "BE Dev": 80, "QA": 40, "DevOps": 40, "PM": 20}
    seen: dict[str, int] = {}
    for role in roles:
        seen[role] = seen.get(role, 0) + 1
    return [
        {"role": role, "count": count, "hours_per_sprint": hour_map.get(role, 60)}
        for role, count in seen.items()
    ]


def SprintAllocatorTool(classified_stories: list[dict], team_composition: list[dict]) -> list[dict]:
    """
    Distribute classified stories across sprints and assemble sprint objects.
    MVP stories fill Sprints 1-4; post-MVP stories go to Sprints 5-6.
    """
    mvp_stories     = [s for s in classified_stories if s.get("is_mvp")]
    postmvp_stories = [s for s in classified_stories if not s.get("is_mvp")]

    sprint_stories: dict[int, list[dict]] = {i: [] for i in range(1, _TOTAL_SPRINTS + 1)}
    for idx, story in enumerate(mvp_stories):
        sprint_stories[(idx % _MVP_CUTOFF_SPRINT) + 1].append(story)
    for idx, story in enumerate(postmvp_stories):
        sprint_stories[_MVP_CUTOFF_SPRINT + (idx % (_TOTAL_SPRINTS - _MVP_CUTOFF_SPRINT)) + 1].append(story)

    role_names = [m["role"] for m in team_composition for _ in range(m["count"])] or ["BE Dev", "FE Dev", "QA", "DevOps"]
    hours_per_sprint = sum(m["count"] * m["hours_per_sprint"] for m in team_composition) or 160

    sprints: list[dict] = []
    for sprint_num in range(1, _TOTAL_SPRINTS + 1):
        stories: list[dict] = []
        for story_idx, s in enumerate(sprint_stories[sprint_num]):
            stories.append(
                {
                    "story_id": f"S{sprint_num}-{story_idx + 1:02d}",
                    "title": s["title"],
                    "description": s["description"],
                    "acceptance_criteria": s["acceptance_criteria"],
                    "story_points": s["story_points"],
                    "role": role_names[story_idx % len(role_names)],
                    "req_id": s["req_id"],
                }
            )
        stories.append(
            {
                "story_id": f"S{sprint_num}-00",
                "title": f"Sprint {sprint_num} setup & grooming",
                "description": "Sprint kickoff, backlog grooming, and technical design for sprint goals.",
                "acceptance_criteria": [
                    "All tasks estimated and assigned.",
                    "Design docs reviewed by tech lead.",
                ],
                "story_points": 2,
                "role": "PM",
                "req_id": "INFRA",
            }
        )
        total_points = sum(s["story_points"] for s in stories)
        sprints.append(
            {
                "sprint_number": sprint_num,
                "sprint_name": f"Sprint {sprint_num}",
                "goal": f"Deliver sprint {sprint_num} scope.",
                "features": list({s["title"] for s in stories if s["req_id"] != "INFRA"}),
                "stories": stories,
                "total_points": total_points,
                "man_hours": hours_per_sprint,
                "is_mvp_cutoff": sprint_num == _MVP_CUTOFF_SPRINT,
            }
        )
    return sprints


# ---------------------------------------------------------------------------
# LLM prompt (active when an API key is configured)
# ---------------------------------------------------------------------------

def _build_prompt(functional_requirements: list[dict], recommended_team: dict) -> str:
    frs_json  = json.dumps(functional_requirements, indent=2)
    team_json = json.dumps(recommended_team, indent=2)
    return f"""You are a senior agile delivery consultant.
Using StoryDecomposerTool, StoryPointerTool, MVPClassifierTool, TeamSizerTool, and SprintAllocatorTool,
generate a complete sprint plan from the inputs below.

FUNCTIONAL REQUIREMENTS:
{frs_json}

RECOMMENDED TEAM:
{team_json}

Return ONLY a valid JSON object with this structure:
{{
  "total_sprints": 6,
  "sprint_duration_weeks": 2,
  "total_story_points": <int>,
  "total_man_hours": <int>,
  "mvp_cutoff_sprint": 4,
  "team_composition": [{{"role": <str>, "count": <int>, "hours_per_sprint": <int>}}],
  "technology_stack": [{{"component": <str>, "technology": <str>, "rationale": <str>}}],
  "sprints": [
    {{
      "sprint_number": <int>, "sprint_name": <str>, "goal": <str>,
      "features": [<str>],
      "stories": [
        {{"story_id": <str>, "title": <str>, "description": <str>,
          "acceptance_criteria": [<str>], "story_points": <int>, "role": <str>, "req_id": <str>}}
      ],
      "total_points": <int>, "man_hours": <int>, "is_mvp_cutoff": <bool>
    }}
  ],
  "risk_register": [
    {{"risk_id": <str>, "description": <str>, "category": <str>,
      "severity": <str>, "mitigation": <str>, "sprint_impacted": <int|null>}}
  ],
  "generated_at": "<ISO timestamp>"
}}
"""


# ---------------------------------------------------------------------------
# Main node
# ---------------------------------------------------------------------------

def sprint_plan_node(state: dict) -> dict:
    """
    LLM node that orchestrates 5 internal tools to generate a sprint plan.

    Tool execution order (fallback pipeline):
      1. StoryDecomposerTool  — FR list → raw user stories
      2. StoryPointerTool     — raw stories → pointed stories
      3. MVPClassifierTool    — pointed stories → MVP-tagged stories
      4. TeamSizerTool        — recommended_team → team composition
      5. SprintAllocatorTool  — tagged stories + team → sprint objects
    """
    analyser_output: dict[str, Any] = state.get("analyser_output") or {}
    functional_requirements: list[dict] = analyser_output.get("functional_requirements", [])
    recommended_team: dict = analyser_output.get("recommended_team", {})

    # Run tool pipeline to build the deterministic fallback
    raw_stories      = StoryDecomposerTool(functional_requirements)
    pointed_stories  = StoryPointerTool(raw_stories)
    tagged_stories   = MVPClassifierTool(pointed_stories, _MVP_CUTOFF_SPRINT)
    team_composition = TeamSizerTool(recommended_team)
    sprints          = SprintAllocatorTool(tagged_stories, team_composition)

    fallback: SprintPlan = {
        "total_sprints": _TOTAL_SPRINTS,
        "sprint_duration_weeks": _SPRINT_DURATION_WEEKS,
        "total_story_points": sum(s["total_points"] for s in sprints),
        "total_man_hours": sum(s["man_hours"] for s in sprints),
        "mvp_cutoff_sprint": _MVP_CUTOFF_SPRINT,
        "team_composition": team_composition,
        "technology_stack": [],
        "sprints": sprints,
        "risk_register": [],
        "generated_at": _now_iso(),
    }

    # Attempt LLM call; returns fallback automatically if no key is set
    prompt = _build_prompt(functional_requirements, recommended_team)
    result = call_structured_json(prompt, fallback)

    if not result.get("generated_at"):
        result["generated_at"] = _now_iso()

    return {"sprint_plan": result}
