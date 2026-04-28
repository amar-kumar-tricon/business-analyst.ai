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


def analyse_node(state: AnalyserState) -> dict:
    """Build the Stage-1 analyser output JSON.

    This function always returns valid output.
    If LLM is configured, it can improve summary/team/open-questions.
    """
    score = state["score"]
    lines = _collect_lines(state)
    requirements = _build_functional_requirements(lines)
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
            "size": max(3, min(8, len(requirements) // 2 + 2)),
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

    llm_prompt = (
        "Improve this analysis output while keeping schema identical. "
        "Return strict JSON with keys executive_summary,project_overview,"
        "functional_requirements,risks,recommended_team,open_questions,"
        "completeness_score,assumptions_made.\n"
        f"Current output: {analyser_output}"
    )
    improved = call_structured_json(llm_prompt, fallback=analyser_output)
    if isinstance(improved, dict):
        # Safety: keep deterministic completeness score and only accept dict shape.
        improved["completeness_score"] = score
        analyser_output = {**analyser_output, **improved}

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
                },
                "timestamp": _now_iso(),
            }
        ],
    }
