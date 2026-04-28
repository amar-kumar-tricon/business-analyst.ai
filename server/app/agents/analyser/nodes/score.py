from __future__ import annotations

from collections import Counter

from app.services.llm_gateway import call_structured_json
from app.shared.state_types import AnalyserState


CRITERION_NAMES = [
    "functional_requirements",
    "business_logic",
    "existing_system",
    "target_audience",
    "architecture_context",
    "nfrs",
    "timeline_budget",
    "visual_assets",
]


CRITERION_WEIGHTS = {
    "functional_requirements": 0.20,
    "business_logic": 0.15,
    "existing_system": 0.15,
    "target_audience": 0.10,
    "architecture_context": 0.15,
    "nfrs": 0.10,
    "timeline_budget": 0.10,
    "visual_assets": 0.05,
}


# Each inner set represents one evidence "bucket" for the criterion.
# Coverage = matched_buckets / total_buckets.
CRITERION_BUCKETS = {
    "functional_requirements": [
        {"functional requirement", "user story", "shall", "must"},
        {"acceptance criteria", "acceptance", "definition of done"},
        {"workflow", "journey", "process flow"},
    ],
    "business_logic": [
        {"business rule", "policy", "eligibility", "validation"},
        {"calculation", "formula", "pricing", "tax"},
        {"decision", "approval", "exception"},
    ],
    "existing_system": [
        {"current system", "as-is", "legacy", "existing"},
        {"integration", "api", "interface", "dependency"},
        {"data migration", "migration", "source system"},
    ],
    "target_audience": [
        {"user", "persona", "stakeholder", "actor"},
        {"admin", "customer", "operator", "manager"},
        {"accessibility", "a11y", "usability"},
    ],
    "architecture_context": [
        {"architecture", "component", "service", "module"},
        {"deployment", "environment", "infrastructure", "cloud"},
        {"security", "auth", "authorization", "compliance"},
    ],
    "nfrs": [
        {"performance", "latency", "throughput", "sla"},
        {"availability", "reliability", "resilience", "backup"},
        {"scalability", "maintainability", "monitoring", "observability"},
    ],
    "timeline_budget": [
        {"timeline", "milestone", "deadline", "schedule"},
        {"budget", "cost", "estimate", "funding"},
        {"phase", "sprint", "release plan"},
    ],
    "visual_assets": [
        {"wireframe", "mockup", "prototype", "figma"},
        {"ui", "ux", "screen", "layout"},
        {"brand", "style guide", "design system"},
    ],
}


def _normalize(text: str) -> str:
    """Make text lowercase and remove repeated spaces for stable matching."""
    return " ".join(text.lower().split())


def _collect_project_text(state: AnalyserState) -> str:
    """Combine all parsed sections into one searchable text block."""
    parts: list[str] = []
    for doc in state.get("parsed_documents", []):
        parts.append(doc.get("file_name", ""))
        for section in doc.get("sections", []):
            parts.append(section.get("section_heading") or "")
            parts.append(section.get("content") or "")

    return _normalize("\n".join(parts))


def _bucket_match_count(project_text: str, buckets: list[set[str]]) -> tuple[int, list[str]]:
    """Count how many evidence buckets are present in the text."""
    matched_indices: list[str] = []

    for idx, bucket in enumerate(buckets, start=1):
        if any(keyword in project_text for keyword in bucket):
            matched_indices.append(f"b{idx}")

    return len(matched_indices), matched_indices


def _criterion_reasoning(
    criterion: str,
    matched_buckets: int,
    total_buckets: int,
    matched_labels: list[str],
    top_terms: list[str],
) -> str:
    """Create a human-readable explanation for one criterion score."""
    missing = total_buckets - matched_buckets
    coverage_pct = round((matched_buckets / total_buckets) * 100, 1) if total_buckets else 0.0
    terms_txt = ", ".join(top_terms) if top_terms else "none"
    matched_txt = ", ".join(matched_labels) if matched_labels else "none"
    return (
        f"Coverage for {criterion}: {matched_buckets}/{total_buckets} buckets "
        f"({coverage_pct}%). Matched buckets: {matched_txt}. "
        f"Missing buckets: {missing}. Frequent evidence terms: {terms_txt}."
    )


def _top_evidence_terms(project_text: str, keywords: set[str]) -> list[str]:
    """Return the most frequent matched keywords for transparency."""
    counts: Counter[str] = Counter()
    for term in keywords:
        if term in project_text:
            counts[term] = project_text.count(term)
    return [term for term, _ in counts.most_common(3)]


def score_node(state: AnalyserState) -> dict:
    """Compute Stage-1 completeness score.

    Step order for learners:
    1. Build baseline deterministic score from keyword coverage.
    2. Ask LLM for optional refined score JSON.
    3. Use LLM values only if valid; otherwise keep deterministic result.
    """
    project_text = _collect_project_text(state)

    if not project_text.strip():
        score = {
            "functional_requirements": 0.0,
            "business_logic": 0.0,
            "existing_system": 0.0,
            "target_audience": 0.0,
            "architecture_context": 0.0,
            "nfrs": 0.0,
            "timeline_budget": 0.0,
            "visual_assets": 0.0,
            "weighted_total": 0.0,
            "per_criterion_reasoning": {
                name: "No parsed text available yet; ingestion/parser output is empty."
                for name in CRITERION_NAMES
            },
        }
        return {"score": score, "needs_enrichment": True}

    criteria_scores: dict[str, float] = {}
    reasoning: dict[str, str] = {}

    for criterion in CRITERION_NAMES:
        buckets = CRITERION_BUCKETS[criterion]
        matched_count, matched_labels = _bucket_match_count(project_text, buckets)

        criterion_score = round(matched_count / len(buckets), 3)
        criteria_scores[criterion] = criterion_score

        all_terms = set().union(*buckets)
        top_terms = _top_evidence_terms(project_text, all_terms)
        reasoning[criterion] = _criterion_reasoning(
            criterion=criterion,
            matched_buckets=matched_count,
            total_buckets=len(buckets),
            matched_labels=matched_labels,
            top_terms=top_terms,
        )

    weighted_total = round(
        sum(criteria_scores[name] * CRITERION_WEIGHTS[name] for name in CRITERION_NAMES) * 10,
        2,
    )

    score = {
        **criteria_scores,
        "weighted_total": weighted_total,
        "per_criterion_reasoning": reasoning,
    }

    llm_prompt = (
        "You are scoring BRD completeness. Return strict JSON with keys: "
        "functional_requirements,business_logic,existing_system,target_audience,"
        "architecture_context,nfrs,timeline_budget,visual_assets,weighted_total,"
        "per_criterion_reasoning.\n"
        f"Use this baseline score and improve if justified:\n{score}\n"
        f"Project text:\n{project_text[:6000]}"
    )
    llm_score = call_structured_json(llm_prompt, fallback=score)

    # Keep result safe: only accept expected keys and numeric ranges.
    final_score = score
    try:
        keys_ok = all(name in llm_score for name in CRITERION_NAMES + ["weighted_total", "per_criterion_reasoning"])
        if keys_ok:
            validated = {name: float(llm_score[name]) for name in CRITERION_NAMES}
            validated_weighted = float(llm_score["weighted_total"])
            if 0.0 <= validated_weighted <= 10.0 and all(0.0 <= v <= 1.0 for v in validated.values()):
                final_score = {
                    **validated,
                    "weighted_total": round(validated_weighted, 2),
                    "per_criterion_reasoning": llm_score.get("per_criterion_reasoning", score["per_criterion_reasoning"]),
                }
    except Exception:
        final_score = score

    return {
        "score": final_score,
        "needs_enrichment": final_score["weighted_total"] <= 5.0,
    }
