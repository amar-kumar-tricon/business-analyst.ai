"""
Sprint Planning Agent — generate_plan node
==========================================

Reads `analyser_output` (Stage 1) and `architecture_output` (Stage 3, may be
mocked) from the shared graph state and produces a complete `SprintPlan`.

When no LLM key is configured the node falls back to a deterministic rule-based
plan so local development is never blocked.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from app.services.llm_gateway import call_structured_json
from app.shared.state_types import SprintState

if TYPE_CHECKING:
    pass


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_HOURS_PER_POINT = 4          # 1 story point ≈ 4 man-hours
_POINTS_PER_SPRINT = 30       # team velocity per 2-week sprint
_MVP_COVERAGE = 0.65          # must_have + should_have up to 65 % → MVP cut-off

_ROLE_MAP = {
    "must_have": "Backend Developer",
    "should_have": "Frontend Developer",
    "good_to_have": "QA Engineer",
}


def _moscow_to_points(moscow: str, idx: int) -> int:
    """Assign story points based on MoSCoW priority and position."""
    base = {"must_have": 8, "should_have": 5, "good_to_have": 3}.get(moscow, 5)
    # Vary slightly so every story isn't identical
    return base + (idx % 3)


def _build_fallback_plan(analyser_output: dict, architecture_output: dict | None) -> dict:
    """
    Build a deterministic sprint plan from the analyser functional requirements.
    Used when no LLM key is available.
    """
    reqs: list[dict] = analyser_output.get("functional_requirements", [])
    risks: list[dict] = analyser_output.get("risks", [])
    team: dict = analyser_output.get("recommended_team", {})

    # Build one story per requirement
    stories: list[dict] = []
    for idx, req in enumerate(reqs):
        moscow = req.get("moscow", "should_have")
        points = _moscow_to_points(moscow, idx)
        story: dict = {
            "story_id": f"STORY-{idx + 1:03d}",
            "title": req.get("description", f"Story {idx + 1}")[:80],
            "description": req.get("description", ""),
            "acceptance_criteria": req.get("acceptance_hints", ["Feature works as specified."]),
            "story_points": points,
            "man_hours": points * _HOURS_PER_POINT,
            "role": _ROLE_MAP.get(moscow, "Backend Developer"),
            "moscow": moscow,
            "sprint_number": 0,   # assigned below
            "is_mvp": moscow in {"must_have", "should_have"},
            "source_req_id": req.get("req_id"),
        }
        stories.append(story)

    if not stories:
        # Minimal fallback when analyser produced no requirements
        stories = [
            {
                "story_id": "STORY-001",
                "title": "Define project baseline and acceptance criteria",
                "description": "Capture baseline scope and acceptance test plan.",
                "acceptance_criteria": ["Baseline document approved by stakeholders."],
                "story_points": 5,
                "man_hours": 20,
                "role": "Business Analyst",
                "moscow": "must_have",
                "sprint_number": 1,
                "is_mvp": True,
                "source_req_id": None,
            }
        ]

    # ── Allocate stories to sprints ──────────────────────────────────────────
    sprints_map: dict[int, list[dict]] = {}
    current_sprint = 1
    current_points = 0

    for story in stories:
        if current_points + story["story_points"] > _POINTS_PER_SPRINT:
            current_sprint += 1
            current_points = 0
        story["sprint_number"] = current_sprint
        current_points += story["story_points"]
        sprints_map.setdefault(current_sprint, []).append(story)

    total_sprints = max(sprints_map.keys()) if sprints_map else 1

    # ── Determine MVP cut-off sprint ─────────────────────────────────────────
    mvp_stories = [s for s in stories if s["is_mvp"]]
    mvp_points = sum(s["story_points"] for s in mvp_stories)
    total_points = sum(s["story_points"] for s in stories)
    # Find the sprint where cumulative points first cover MVP
    mvp_cutoff = total_sprints
    running = 0
    for sn in sorted(sprints_map.keys()):
        running += sum(s["story_points"] for s in sprints_map[sn])
        if running >= mvp_points:
            mvp_cutoff = sn
            break

    # ── Build sprint objects ──────────────────────────────────────────────────
    sprint_objects: list[dict] = []
    for sn in sorted(sprints_map.keys()):
        sprint_stories = sprints_map[sn]
        sp = sum(s["story_points"] for s in sprint_stories)
        hrs = sum(s["man_hours"] for s in sprint_stories)
        sprint_objects.append(
            {
                "sprint_number": sn,
                "sprint_goal": f"Sprint {sn} — deliver {len(sprint_stories)} user stories ({sp} pts)",
                "stories": sprint_stories,
                "total_points": sp,
                "total_hours": hrs,
                "start_week": (sn - 1) * 2 + 1,
                "end_week": sn * 2,
            }
        )

    total_man_hours = sum(s["man_hours"] for s in stories)

    # ── Tech stack from architecture output (if available) ───────────────────
    arch_notes = ""
    if architecture_output:
        arch_notes = architecture_output.get("tech_stack_notes", "")

    tech_stack = {
        "frontend": "React 18 / TypeScript",
        "backend": "FastAPI / Python 3.12",
        "database": "SQLite (dev) → PostgreSQL (prod)",
        "agent_framework": "LangGraph + LangChain",
        "notes": arch_notes or "Derived from project architecture context.",
    }

    # ── Team composition ──────────────────────────────────────────────────────
    team_size = team.get("size", 5)
    team_composition = {
        "roles": team.get("roles", ["Backend Developer", "Frontend Developer", "QA Engineer"]),
        "headcount": team_size,
        "breakdown": {
            "Backend Developer": max(1, team_size // 3),
            "Frontend Developer": max(1, team_size // 3),
            "QA Engineer": max(1, team_size // 4),
            "Project Manager": 1,
            "DevOps": 1 if team_size >= 5 else 0,
        },
    }

    # ── Risk register (pass-through from analyser + sprint-specific risks) ───
    risk_register = [
        {
            "risk_id": r.get("risk_id", f"RISK-{i + 1:03d}"),
            "description": r.get("description", ""),
            "category": r.get("category", "delivery"),
            "severity": r.get("severity", "medium"),
            "mitigation": r.get("mitigation", "Monitor and review at next sprint retrospective."),
            "sprint_impact": "All sprints",
        }
        for i, r in enumerate(risks)
    ]
    # Add sprint-specific scope creep risk
    risk_register.append(
        {
            "risk_id": f"RISK-SP-{len(risk_register) + 1:03d}",
            "description": "Scope creep may shift story point estimates in later sprints.",
            "category": "delivery",
            "severity": "medium",
            "mitigation": "Freeze scope at MVP cut-off; defer new items to next version.",
            "sprint_impact": f"Sprint {mvp_cutoff + 1} onwards",
        }
    )

    return {
        "total_sprints": total_sprints,
        "total_story_points": total_points,
        "total_man_hours": total_man_hours,
        "mvp_cutoff_sprint": mvp_cutoff,
        "sprint_duration_weeks": 2,
        "team_composition": team_composition,
        "tech_stack": tech_stack,
        "risk_register": risk_register,
        "sprints": sprint_objects,
        "generated_at": _now_iso(),
    }


# ──────────────────────────────────────────────
# Node entry-point
# ──────────────────────────────────────────────

def generate_plan_node(state: SprintState) -> dict:
    """
    Generate a full sprint plan from finalised analyser and architecture outputs.

    Decision logic:
    - Always build a deterministic fallback plan first (guarantees a valid plan).
    - If an LLM key is configured, send the fallback plan + context to the LLM
      and ask it to improve the plan.  The LLM response must match the SprintPlan
      schema; if it does not, the fallback is preserved.

    The `architecture_output` may be a mocked dict when the Architecture Agent is
    still under development.  The node handles both cases transparently.
    """
    analyser_output: dict = state.get("analyser_output") or {}
    architecture_output: dict | None = state.get("architecture_output")

    # ── Step 1: Deterministic fallback plan ───────────────────────────────────
    fallback_plan = _build_fallback_plan(analyser_output, architecture_output)

    # ── Step 2: Optional LLM enrichment ──────────────────────────────────────
    arch_summary = ""
    if architecture_output:
        diagrams = architecture_output.get("diagrams", [])
        arch_summary = (
            f"Architecture diagrams available: {[d.get('title') for d in diagrams]}. "
            f"Tech notes: {architecture_output.get('tech_stack_notes', '')}"
        )

    llm_prompt = (
        "You are a Sprint Planning Agent. Using the analysed requirements and architecture context below, "
        "produce an improved sprint plan. Return STRICT JSON matching the SprintPlan schema:\n"
        "{ total_sprints, total_story_points, total_man_hours, mvp_cutoff_sprint, "
        "sprint_duration_weeks, team_composition, tech_stack, risk_register, sprints, generated_at }\n\n"
        f"Analyser output summary:\n"
        f"- Executive summary: {analyser_output.get('executive_summary', '')[:300]}\n"
        f"- Functional requirements count: {len(analyser_output.get('functional_requirements', []))}\n"
        f"- Risks: {len(analyser_output.get('risks', []))}\n"
        f"- Recommended team: {analyser_output.get('recommended_team', {})}\n\n"
        f"Architecture context: {arch_summary or 'Not yet available (mocked).'}\n\n"
        f"Current fallback plan (improve this):\n{fallback_plan}"
    )

    improved = call_structured_json(llm_prompt, fallback=fallback_plan)

    # Safety check: ensure we always have a valid plan dict
    sprint_plan = improved if isinstance(improved, dict) and "sprints" in improved else fallback_plan
    # Always stamp generated_at in case LLM didn't
    sprint_plan["generated_at"] = _now_iso()

    return {
        "sprint_plan": sprint_plan,
        "streaming_events": [
            {
                "event_id": str(uuid.uuid4()),
                "type": "sprint_plan_generated",
                "node": "generate_plan_node",
                "payload": {
                    "total_sprints": sprint_plan["total_sprints"],
                    "total_story_points": sprint_plan["total_story_points"],
                    "total_man_hours": sprint_plan["total_man_hours"],
                    "mvp_cutoff_sprint": sprint_plan["mvp_cutoff_sprint"],
                    "used_mock_architecture": architecture_output is None
                    or architecture_output.get("is_mocked", False),
                },
                "timestamp": _now_iso(),
            }
        ],
    }

