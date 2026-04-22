"""
app.agents.analyser.agent
=========================
STAGE 1 — Document Analyser Agent.

Inputs  (from GraphState):  uploaded_documents, additional_context
Outputs (into GraphState):  analyser_output (schemas.analyser.AnalyserResult)

Flow:
    1. score the document using DocumentScorerTool   (1–10)
    2. if score < 6  → run EnrichmentTool
    3. in parallel:  MoSCoWClassifierTool, RiskExtractorTool, TeamRecommenderTool
    4. compose final AnalyserResult JSON via function-calling on the LLM

See BRD §4.2 for full spec.
"""
from __future__ import annotations

from typing import Any

from app.agents.analyser import prompts, tools
from app.agents.llm_factory import build_llm
from app.agents.state import GraphState
from app.schemas.analyser import (
    AnalyserResult,
    CompletenessScore,
    FunctionalRequirements,
    ProjectOverview,
)

AGENT_ID = "analyser"


async def analyser_node(state: GraphState) -> dict[str, Any]:
    """LangGraph node function. Must return a partial GraphState dict."""
    llm = build_llm(AGENT_ID, state)  # noqa: F841 — used once implemented

    raw_text = "\n\n".join(c["text"] for c in state.get("uploaded_documents", []))
    raw_text += "\n\n" + (state.get("additional_context") or "")

    # 1) Score
    score, breakdown = tools.score_document(raw_text)

    # 2) Conditionally enrich
    if score < 6:
        raw_text = await tools.enrich(raw_text, llm)

    # 3) Build structured output
    #    TODO: replace the stub below with a function-calling prompt
    #    that returns JSON conforming to AnalyserResult. Use:
    #        llm.with_structured_output(AnalyserResult).ainvoke(prompts.SYSTEM + raw_text)
    result = AnalyserResult(
        executive_summary="TODO: generate via LLM",
        project_overview=ProjectOverview(objective="", scope="", out_of_scope=""),
        functional_requirements=FunctionalRequirements(),
        risks=[],
        recommended_team=[],
        open_questions=[],
        completeness_score=CompletenessScore(total=score, breakdown=breakdown),
        enriched=score < 6,
    )

    return {"analyser_output": result, "current_stage": "analyse", "open_questions": result.open_questions}


# re-export for convenience
__all__ = ["analyser_node", "AGENT_ID", "prompts", "tools"]
