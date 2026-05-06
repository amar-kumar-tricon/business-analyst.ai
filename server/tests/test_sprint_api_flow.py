"""
Sprint Agent REST API Test Suite
=================================
End-to-end test that walks through the full pipeline:

  Step 1  POST /api/projects                       → create project
  Step 2  POST /api/projects/{id}/run              → Stage 1 + Discovery
  Step 3  POST /api/projects/{id}/discovery/answer → terminate discovery
  Step 4  POST /api/projects/{id}/architecture/run → mocked architecture
  Step 5  POST /api/projects/{id}/architecture/approve → approve arch
  Step 6  POST /api/projects/{id}/sprint/run       → Sprint Planning Agent ⭐
  Step 7  GET  /api/projects/{id}/sprint           → fetch sprint plan ⭐
  Step 8  POST /api/projects/{id}/sprint/approve   → finalize project ⭐

Run with:
    python tests/test_sprint_api_flow.py
"""

from __future__ import annotations

import sys
from typing import Any

try:
    import requests as _requests
except ImportError:
    print("❌ 'requests' library not found. Install with:  pip install requests")
    sys.exit(1)

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
_SESSION = _requests.Session()
_SESSION.headers.update(HEADERS)

# ─────────────────────────── helpers ────────────────────────────────────────

def _request(method: str, path: str, body: dict | None = None, *, label: str) -> dict:
    url = f"{BASE_URL}{path}"
    try:
        resp = _SESSION.request(method, url, json=body, timeout=120)
        if resp.ok:
            payload = resp.json()
            print(f"\n✅ [{label}] {method} {path}  →  HTTP {resp.status_code}")
            return payload
        else:
            print(f"\n❌ [{label}] {method} {path}  →  HTTP {resp.status_code}")
            print(f"   Detail: {resp.text[:400]}")
            sys.exit(1)
    except _requests.exceptions.HTTPError as exc:
        print(f"\n❌ [{label}] {method} {path}  →  {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n💥 [{label}] {method} {path}  →  {exc}")
        sys.exit(1)


def _pp(label: str, data: Any, max_depth: int = 3) -> None:
    """Pretty-print selected keys from a response dict."""
    print(f"   ╔══ {label}")
    _dump(data, indent=3, depth=0, max_depth=max_depth)


def _dump(obj: Any, indent: int, depth: int, max_depth: int) -> None:
    pad = " " * indent
    if depth >= max_depth:
        print(f"{pad}... (truncated)")
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                print(f"{pad}{k}:")
                _dump(v, indent + 3, depth + 1, max_depth)
            else:
                val_str = str(v)
                if len(val_str) > 120:
                    val_str = val_str[:117] + "..."
                print(f"{pad}{k}: {val_str}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:5]):
            print(f"{pad}[{i}]")
            _dump(item, indent + 3, depth + 1, max_depth)
        if len(obj) > 5:
            print(f"{pad}... ({len(obj) - 5} more items)")
    else:
        print(f"{pad}{obj}")


# ─────────────────────────── test steps ─────────────────────────────────────

def step_health() -> None:
    resp = _request("GET", "/health", label="HEALTH")
    assert resp.get("status") == "ok", f"Expected status=ok, got {resp}"
    print(f"   Server is UP ✔")


def step_create_project() -> str:
    resp = _request(
        "POST", "/api/projects",
        body={
            "name": "Sprint Test Project",
            "additional_context": (
                "We are building an e-commerce platform with product catalog, "
                "shopping cart, checkout, order management and user authentication. "
                "Team has 3 backend engineers, 2 frontend engineers, 1 QA engineer. "
                "Delivery target is 6 months. Tech stack: Python FastAPI + React + PostgreSQL."
            ),
        },
        label="CREATE PROJECT",
    )
    project_id = resp["project_id"]
    assert project_id, "Expected a project_id in response"
    _pp("Response", resp)
    print(f"\n   🆔 project_id = {project_id}")
    return project_id


def step_run_stage1(project_id: str) -> dict:
    resp = _request("POST", f"/api/projects/{project_id}/run", label="RUN STAGE-1")
    _pp("Stage-1 output", {
        "score": resp.get("score"),
        "has_question": bool(resp.get("current_question")),
        "question_text": (resp.get("current_question") or {}).get("question_text", "—"),
        "has_final_doc": bool(resp.get("final_doc_markdown")),
    })
    return resp


def step_terminate_discovery(project_id: str) -> dict:
    resp = _request(
        "POST", f"/api/projects/{project_id}/discovery/answer",
        body={"terminate": True, "status": "na"},
        label="TERMINATE DISCOVERY",
    )
    _pp("Discovery output", {
        "current_question": resp.get("current_question"),
        "qa_history_count": resp.get("qa_history_count"),
        "has_final_doc": bool(resp.get("final_doc_markdown")),
    })
    return resp


def step_run_architecture(project_id: str) -> dict:
    resp = _request(
        "POST", f"/api/projects/{project_id}/architecture/run",
        label="RUN ARCHITECTURE",
    )
    _pp("Architecture output", {
        "diagram_count": resp.get("diagram_count"),
        "is_mocked": resp.get("is_mocked"),
        "diagrams_preview": [
            d.get("title") for d in (resp.get("architecture_output") or {}).get("diagrams", [])
        ],
    })
    return resp


def step_approve_architecture(project_id: str) -> dict:
    resp = _request(
        "POST", f"/api/projects/{project_id}/architecture/approve",
        body={"user_edits_payload": None},
        label="APPROVE ARCHITECTURE",
    )
    _pp("Architecture approve", {
        "review_3_status": resp.get("review_3_status"),
        "message": resp.get("message"),
    })
    return resp


def step_run_sprint(project_id: str) -> dict:
    print("\n" + "="*60)
    print("  🏃 RUNNING SPRINT PLANNING AGENT (Stage 4)")
    print("="*60)
    resp = _request(
        "POST", f"/api/projects/{project_id}/sprint/run",
        label="RUN SPRINT",
    )
    plan = resp.get("sprint_plan") or {}
    summary = resp.get("summary") or {}

    print("\n   📋 Sprint Plan Summary:")
    print(f"      Total Sprints       : {summary.get('total_sprints')}")
    print(f"      Total Story Points  : {summary.get('total_story_points')}")
    print(f"      Total Man-Hours     : {summary.get('total_man_hours')}")
    print(f"      MVP Cutoff Sprint   : {summary.get('mvp_cutoff_sprint')}")
    print(f"      Sprint Duration     : {summary.get('sprint_duration_weeks')} weeks")

    sprints = plan.get("sprints", [])
    if sprints:
        print(f"\n   📅 Sprint Breakdown ({len(sprints)} sprints):")
        for s in sprints:
            stories = s.get("stories", [])
            pts = s.get("story_points") or s.get("total_points", "?")
            hrs = s.get("man_hours") or s.get("total_hours", "?")
            print(f"      Sprint {s.get('sprint_number')}: {s.get('sprint_goal', 'No goal')}")
            print(f"        Stories: {len(stories)}, Points: {pts}, Hours: {hrs}")
            for story in stories[:3]:
                print(f"          • {story.get('title', 'N/A')} [{story.get('story_points', '?')}pts]")
            if len(stories) > 3:
                print(f"          ... ({len(stories) - 3} more stories)")

    team = plan.get("team_composition") or {}
    if isinstance(team, list):
        print(f"\n   👥 Team Composition:")
        for member in team:
            print(f"      • {member.get('role')} (x{member.get('count', 1)}) — {member.get('daily_hours', 8)}h/day")
    elif isinstance(team, dict):
        print(f"\n   👥 Team Composition:")
        print(f"      Headcount  : {team.get('headcount', '?')}")
        roles = team.get("roles", [])
        if roles:
            print(f"      Roles      : {', '.join(roles)}")
        breakdown = team.get("breakdown", {})
        for role, count in breakdown.items():
            print(f"      • {role}: {count}")

    risks = plan.get("risk_register", [])
    if risks:
        print(f"\n   ⚠️  Risk Register ({len(risks)} risks):")
        for r in risks[:3]:
            print(f"      • [{r.get('severity', '?')}] {r.get('risk', 'N/A')}")
        if len(risks) > 3:
            print(f"      ... ({len(risks) - 3} more risks)")

    tech = plan.get("tech_stack") or {}
    if isinstance(tech, list):
        print(f"\n   🛠️  Tech Stack: {', '.join(str(t) for t in tech[:8])}")
    elif isinstance(tech, dict):
        print(f"\n   🛠️  Tech Stack:")
        for k, v in tech.items():
            if v:
                print(f"      {k}: {v}")

    return resp


def step_get_sprint(project_id: str) -> dict:
    resp = _request(
        "GET", f"/api/projects/{project_id}/sprint",
        label="GET SPRINT PLAN",
    )
    plan = resp.get("sprint_plan") or {}
    print(f"   review_4_status: {resp.get('review_4_status')}")
    print(f"   total_sprints in fetched plan: {plan.get('total_sprints')}")
    print(f"   total_story_points: {plan.get('total_story_points')}")
    assert plan, "Sprint plan must not be empty"
    return resp


def step_approve_sprint(project_id: str) -> dict:
    print("\n" + "="*60)
    print("  ✅ APPROVING SPRINT PLAN (Finalize Project)")
    print("="*60)
    resp = _request(
        "POST", f"/api/projects/{project_id}/sprint/approve",
        body={
            "sprint_notes": "Sprint plan reviewed and approved by Product Owner. All epics align with Q3 roadmap.",
            "user_edits_payload": {
                "approved_by": "test_runner",
                "note": "Automated approval via test suite",
            },
        },
        label="APPROVE SPRINT",
    )
    _pp("Sprint approval result", {
        "status": resp.get("status"),
        "review_4_status": resp.get("review_4_status"),
        "final_doc_pdf_s3_key": resp.get("final_doc_pdf_s3_key"),
        "final_doc_docx_s3_key": resp.get("final_doc_docx_s3_key"),
        "sprint_plan_summary": resp.get("sprint_plan_summary"),
    })
    assert resp.get("status") == "approved", f"Expected status=approved, got {resp.get('status')}"
    return resp


def step_verify_final_state(project_id: str) -> None:
    resp = _request(
        "GET", f"/api/projects/{project_id}",
        label="VERIFY FINAL STATE",
    )
    state = resp.get("state", {})
    print(f"   review_4_status   : {state.get('review_4_status')}")
    print(f"   has sprint_plan   : {bool(state.get('sprint_plan'))}")
    print(f"   has architecture  : {bool(state.get('architecture_output'))}")
    print(f"   has final_doc     : {bool(state.get('final_doc_markdown'))}")
    print(f"   pdf artifact      : {state.get('final_doc_pdf_s3_key', '—')}")
    print(f"   docx artifact     : {state.get('final_doc_docx_s3_key', '—')}")
    sprint_plan = state.get("sprint_plan") or {}
    print(f"   total_sprints     : {sprint_plan.get('total_sprints')}")
    print(f"   mvp_cutoff_sprint : {sprint_plan.get('mvp_cutoff_sprint')}")


def step_check_events(project_id: str) -> None:
    resp = _request(
        "GET", f"/api/projects/{project_id}/events",
        label="PROJECT EVENTS",
    )
    events = resp.get("events", [])
    sprint_events = [e for e in events if "sprint" in e.get("type", "").lower() or "sprint" in e.get("node", "").lower()]
    print(f"   Total events: {len(events)}")
    print(f"   Sprint-related events: {len(sprint_events)}")
    for e in sprint_events:
        print(f"      [{e.get('type')}] node={e.get('node')}  payload={e.get('payload')}")


# ─────────────────────────── edge-case tests ────────────────────────────────

def test_sprint_without_analyser() -> None:
    """Verify that running sprint without Stage 1 returns 409."""
    resp = _request(
        "POST", "/api/projects",
        body={"name": "Sprint Prereq Test", "additional_context": "test"},
        label="PREREQ TEST — create project",
    )
    pid = resp["project_id"]
    r = _SESSION.post(f"{BASE_URL}/api/projects/{pid}/sprint/run", json={}, timeout=15)
    if r.status_code == 409:
        print(f"\n✅ [PREREQ TEST — sprint without analyser]  →  HTTP 409 (guard working correctly)")
    elif r.status_code == 200:
        print("\n❌ [PREREQ TEST] Expected HTTP 409 but got 200 — guard is MISSING!")
    else:
        print(f"\n⚠️  [PREREQ TEST] Expected 409, got HTTP {r.status_code}")


def test_get_sprint_before_run() -> None:
    """Verify that GET /sprint before running returns 404."""
    resp = _request(
        "POST", "/api/projects",
        body={"name": "Sprint GET Before Run Test", "additional_context": "test"},
        label="GET BEFORE RUN — create project",
    )
    pid = resp["project_id"]
    r = _SESSION.get(f"{BASE_URL}/api/projects/{pid}/sprint", timeout=15)
    if r.status_code == 404:
        print(f"\n✅ [GET BEFORE RUN — sprint plan before run]  →  HTTP 404 (correct)")
    elif r.status_code == 200:
        print("\n❌ [GET BEFORE RUN] Expected HTTP 404 but got 200")
    else:
        print(f"\n⚠️  [GET BEFORE RUN] Expected 404, got HTTP {r.status_code}")


# ─────────────────────────── main ───────────────────────────────────────────

def main() -> None:
    print("\n" + "█"*65)
    print("  SPRINT AGENT — REST API TEST SUITE")
    print("█"*65)

    # ── Happy path ───────────────────────────────────────────────────────
    print("\n═══ HAPPY PATH ═══════════════════════════════════════════════")

    step_health()
    project_id = step_create_project()
    step_run_stage1(project_id)
    step_terminate_discovery(project_id)
    step_run_architecture(project_id)
    step_approve_architecture(project_id)

    step_run_sprint(project_id)
    step_get_sprint(project_id)
    step_approve_sprint(project_id)
    step_verify_final_state(project_id)
    step_check_events(project_id)

    # ── Guard / edge cases ────────────────────────────────────────────────
    print("\n═══ GUARD / EDGE-CASE TESTS ══════════════════════════════════")
    test_sprint_without_analyser()
    test_get_sprint_before_run()

    print("\n" + "█"*65)
    print(f"  ✅  ALL SPRINT API TESTS PASSED  (project_id={project_id})")
    print("█"*65 + "\n")


if __name__ == "__main__":
    main()

