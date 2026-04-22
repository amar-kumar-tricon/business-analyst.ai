"""
app.agents.discovery.agent
==========================
STAGE 2 — Discovery / QnA Agent.

Behaviour (BRD §4.3):
    * Generate ONE question at a time using `open_questions` + any gaps in the
      current `analyser_output`.
    * The product person answers / defers / marks N-A via the REST endpoint.
    * Each answered question triggers a delta update to `analyser_output`.
    * When there are no more questions to ask, the node returns and the graph
      proceeds to `human_review_2`.

This node is RE-ENTRANT: it may be invoked multiple times as each answer comes in.
"""
from __future__ import annotations

from typing import Any

from app.agents.discovery import prompts, tools  # noqa: F401 — re-exported for tests
from app.agents.llm_factory import build_llm
from app.agents.state import GraphState

AGENT_ID = "discovery"


async def discovery_node(state: GraphState) -> dict[str, Any]:
    llm = build_llm(AGENT_ID, state)  # noqa: F841

    open_qs = list(state.get("open_questions") or [])
    history = list(state.get("discovery_qa") or [])

    if not open_qs:
        # no more questions → done
        return {"current_stage": "discovery"}

    # TODO:
    #   * call tools.generate_next_question(open_qs, history, analyser_output, llm)
    #   * stream the question to WS as {type: 'question', payload: {question}}
    #   * exit and wait for the next /discovery/answer call to re-enter this node.

    next_q = open_qs[0]
    return {"open_questions": open_qs, "current_stage": "discovery", "next_question": next_q}
