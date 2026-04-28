from __future__ import annotations

from datetime import datetime, timezone

from app.shared.state_types import DiscoveryState


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def finalize_doc_node(state: DiscoveryState) -> dict:
    """Render analyser output and discovery decisions into final markdown."""
    ao = state["analyser_output"]
    now = _now_iso()
    weighted = ao.get("completeness_score", {}).get("weighted_total", 0.0)
    overview = ao.get("project_overview", {})

    lines = [
        f"# Business Requirements Analysis",
        f"",
        f"*Generated: {now}*",
        f"",
        f"## Executive Summary",
        f"",
        ao.get("executive_summary", "_No summary yet._"),
        f"",
        f"## Project Overview",
        f"",
        f"- Objective: {overview.get('objective', 'N/A')}",
        f"- Scope: {overview.get('scope', 'N/A')}",
        f"- Out of scope: {overview.get('out_of_scope', 'N/A')}",
        f"",
        f"## Functional Requirements",
        f"",
    ]

    for req in ao.get("functional_requirements", []):
        lines.append(f"- [{req.get('moscow','?').upper()}] {req.get('description', '')}")

    lines += [
        f"",
        f"## Risks",
        f"",
    ]
    for risk in ao.get("risks", []):
        lines.append(f"- [{risk.get('severity','?').upper()}] {risk.get('description', '')}")

    lines += [
        f"",
        f"## Q&A Decisions",
        f"",
    ]
    for qa in state.get("qa_history", []):
        if qa.get("status") == "answered":
            lines.append(f"**Q:** {qa['question']}  ")
            lines.append(f"**A:** {qa.get('answer', '_no answer_')}")
            lines.append(f"")

    lines += [
        f"## Completeness",
        f"",
        f"Current completeness score: **{weighted}/10**",
    ]

    markdown = "\n".join(lines)
    return {"final_doc_markdown": markdown}
