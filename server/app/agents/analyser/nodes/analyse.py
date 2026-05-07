from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.services.llm_gateway import call_structured_json
from app.shared.state_types import AnalyserState


def _now_iso() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _collect_lines(state: AnalyserState) -> list[str]:
    """Collect non-empty lines from parsed docs for simple analysis."""
    lines: list[str] = []
    for doc in state.get("parsed_documents", []):
        for section in doc.get("sections", []):
            content = section.get("content", "")
            for raw_line in content.splitlines():
                line = raw_line.strip()
                if line:
                    lines.append(line)
    return lines


def _build_functional_requirements(lines: list[str]) -> list[dict]:
    """Extract requirement-like lines using easy keyword rules."""
    reqs: list[dict] = []
    idx = 1
    for line in lines:
        low = line.lower()
        if "must" in low or "shall" in low or "should" in low:
            moscow = "must_have" if ("must" in low or "shall" in low) else "should_have"
            reqs.append(
                {
                    "req_id": f"FR-{idx:03d}",
                    "description": line,
                    "moscow": moscow,
                    "acceptance_hints": ["Verify expected output for primary business scenario."],
                    "source": "document",
                    "source_ref": None,
                }
            )
            idx += 1

    if not reqs:
        reqs.append(
            {
                "req_id": "FR-001",
                "description": "Define baseline end-to-end workflow and core user actions.",
                "moscow": "must_have",
                "acceptance_hints": ["Flow can be executed from start to completion."],
                "source": "enrichment",
                "source_ref": "fallback",
            }
        )

    return reqs


def _build_risks(score: dict) -> list[dict]:
    """Create risk entries for low-scoring criteria."""
    risks: list[dict] = []
    idx = 1
    for criterion, value in score.items():
        if criterion in {"weighted_total", "per_criterion_reasoning"}:
            continue
        if isinstance(value, (int, float)) and value < 0.67:
            risks.append(
                {
                    "risk_id": f"RISK-{idx:03d}",
                    "description": f"Low confidence in {criterion.replace('_', ' ')} coverage.",
                    "category": "delivery" if criterion in {"timeline_budget", "nfrs"} else "technical",
                    "severity": "high" if value < 0.34 else "medium",
                    "mitigation": f"Collect additional evidence and run focused review for {criterion}.",
                }
            )
            idx += 1

    if not risks:
        risks.append(
            {
                "risk_id": "RISK-001",
                "description": "No major delivery blockers identified from current documentation.",
                "category": "business",
                "severity": "low",
                "mitigation": "Continue validating assumptions during review checkpoints.",
            }
        )

    return risks


def _build_open_questions(score: dict) -> list[dict]:
    """Generate follow-up questions where confidence is not high yet."""
    questions: list[dict] = []
    idx = 1
    for criterion, value in score.items():
        if criterion in {"weighted_total", "per_criterion_reasoning"}:
            continue
        if isinstance(value, (int, float)) and value < 0.9:
            priority = "high" if value < 0.34 else "medium"
            questions.append(
                {
                    "question_id": f"Q-{idx:03d}",
                    "question": f"What additional details can you provide for {criterion.replace('_', ' ')}?",
                    "priority": priority,
                    "blocked_decisions": [
                        f"Finalize {criterion.replace('_', ' ')} section",
                        "Approve final analysis document",
                    ],
                }
            )
            idx += 1

    return questions[:10]


def _collect_full_text(state: AnalyserState) -> str:
    """Collect all content — prioritises additional_context, then parsed docs."""
    parts: list[str] = []
    # Always include the original project context first
    ctx = state.get("additional_context", "").strip()
    if ctx:
        parts.append(ctx)
    # Then any non-enrichment sections from parsed docs
    for doc in state.get("parsed_documents", []):
        if doc.get("file_name") == "enrichment_notes.md":
            continue
        for section in doc.get("sections", []):
            content = section.get("content", "").strip()
            if content:
                parts.append(content)
    return "\n\n".join(parts)


def analyse_node(state: AnalyserState) -> dict:
    """Build the Stage-1 analyser output JSON.

    When LLM is configured, uses it to extract requirements from the full text.
    Otherwise falls back to keyword-based extraction.
    """
    score = state["score"]
    full_text = _collect_full_text(state)
    lines = _collect_lines(state)

    # ── Step 1: Try LLM extraction first ─────────────────────────────────────
    llm_extract_prompt = (
        "You are a Business Analyst. Extract ALL functional requirements from the text below.\n"
        "Return STRICT JSON: {\"requirements\": [{\"req_id\": \"FR-001\", \"description\": \"...\", "
        "\"moscow\": \"must_have|should_have|good_to_have\", "
        "\"acceptance_hints\": [\"...\"]}]}\n"
        "Extract every distinct feature/capability as a separate requirement. Aim for 10-30 items.\n\n"
        f"TEXT:\n{full_text[:6000]}"
    )
    llm_reqs_result = call_structured_json(
        llm_extract_prompt,
        fallback={"requirements": []},
    )
    llm_reqs = llm_reqs_result.get("requirements", []) if isinstance(llm_reqs_result, dict) else []

    # Validate shape — each item must have req_id and description
    valid_llm_reqs = [
        r for r in llm_reqs
        if isinstance(r, dict) and r.get("req_id") and r.get("description")
    ]

    # ── Step 2: Fall back to keyword rules if LLM gave nothing ───────────────
    requirements = valid_llm_reqs if valid_llm_reqs else _build_functional_requirements(lines)

    risks = _build_risks(score)
    questions = _build_open_questions(score)
    weighted = score.get("weighted_total", 0.0)

    analyser_output = {
        "executive_summary": (
            f"Analysis completed with weighted completeness score {weighted}/10. "
            f"Derived {len(requirements)} functional requirements and {len(risks)} risk items."
        ),
        "project_overview": {
            "objective": "Deliver an implementation-ready requirement baseline.",
            "scope": "Business analysis for Stage 1 and Stage 2 flow.",
            "out_of_scope": "Architecture and sprint planning stages.",
        },
        "functional_requirements": requirements,
        "risks": risks,
        "recommended_team": {
            "roles": ["Business Analyst", "Tech Lead", "QA Engineer"],
            "size": max(3, min(10, len(requirements) // 3 + 2)),
            "rationale": "Team size scales with requirement volume and risk profile.",
        },
        "open_questions": questions,
        "completeness_score": score,
        "assumptions_made": [
            {
                "id": str(uuid.uuid4()),
                "text": "Initial analysis is based on currently available parsed documents.",
                "timestamp": _now_iso(),
            }
        ],
    }

    return {
        "analyser_output": analyser_output,
        "streaming_events": [
            {
                "event_id": str(uuid.uuid4()),
                "type": "analysis_generated",
                "node": "analyse_node",
                "payload": {
                    "requirements": len(requirements),
                    "risks": len(risks),
                    "open_questions": len(questions),
                    "used_llm_extraction": bool(valid_llm_reqs),
                },
                "timestamp": _now_iso(),
            }
        ],
    }
