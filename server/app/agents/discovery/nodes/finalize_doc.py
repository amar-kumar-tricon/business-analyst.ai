from __future__ import annotations

from datetime import datetime, timezone

from app.shared.state_types import DiscoveryState


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def finalize_doc_node(state: DiscoveryState) -> dict:
    """Render analyser_output + qa_history into a markdown document.

    Placeholder: produces a minimal stub markdown so the parent graph can
    proceed to human_review_2 and artifact_export without errors.

    Real impl will:
    - Use a Jinja2 template (app/templates/final_analysis.md.j2).
    - Group functional requirements by MoSCoW bucket.
    - Sort risks by severity.
    - Append a Q&A Decisions section from qa_history (answered only).
    - Add a completeness score section.
    """
    ao = state["analyser_output"]
    now = _now_iso()

    lines = [
        f"# Business Requirements Analysis",
        f"",
        f"*Generated: {now}*",
        f"",
        f"## Executive Summary",
        f"",
        ao.get("executive_summary", "_No summary yet._"),
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

    markdown = "\n".join(lines)
    return {"final_doc_markdown": markdown}
