"""
app.agents.graph
================
The LangGraph pipeline. This single file wires ALL agents together and is the
primary document for how a project flows from upload → finalized.

Diagram (also in the root README):

    document_ingestion
            │
            ▼
    analyser_agent  ────►  human_review_1  (interrupt)
                                 │
                                 ▼
                          discovery_agent  ────►  human_review_2
                                                       │
                                                       ▼
                                                architecture_agent ─► human_review_3
                                                                            │
                                                                            ▼
                                                                     sprint_agent ─► human_review_4
                                                                                          │
                                                                                          ▼
                                                                                     finalized

IMPORTANT USAGE RULES:
    * Every agent node MUST return a *partial* state dict — LangGraph merges it in.
    * Every agent node MUST be a pure function of GraphState; no global mutation.
    * Human approvals are modelled as `interrupt_before=[...]` which pauses the graph;
      the API layer calls `graph.update_state(...)` + `graph.invoke(None, ...)` to resume.
"""
from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.analyser.agent import analyser_node
from app.agents.architecture.agent import architecture_node
from app.agents.discovery.agent import discovery_node
from app.agents.sprint.agent import sprint_node
from app.agents.state import GraphState


def _document_ingestion(state: GraphState) -> dict[str, Any]:
    """Tool node — parses uploaded files + chunks + embeds. Runs before Stage 1.

    TODO:
        * pull raw bytes from S3 for each document
        * call services.document_parser.parse(...)
        * call services.embeddings.chunk_text + embed_chunks
        * upsert into pgvector and populate state['uploaded_documents']
    """
    return {"current_stage": "analyse"}


def _change_propagation(state: GraphState) -> dict[str, Any]:
    """Tool node — on new requirements, decide which stages must re-run.

    TODO:
        * diff old vs new uploaded_documents / additional_context
        * set approval_status[<stage>] = False for affected stages
        * append a ChangeEventLog to state['change_log']
    """
    return {}


# --- Placeholder node shims for human review interrupts --------------------
# `interrupt_before=[...]` in `StateGraph.compile(...)` pauses the graph just
# BEFORE these nodes run. When the UI calls the approve endpoint, we invoke
# `graph.update_state(...)` with any edits and `graph.invoke(None, ...)` to continue.
def _human_review_stub(_: GraphState) -> dict[str, Any]:
    return {}


def build_graph():
    g = StateGraph(GraphState)

    # ---- nodes ----
    g.add_node("document_ingestion", _document_ingestion)
    g.add_node("analyser_agent", analyser_node)
    g.add_node("human_review_1", _human_review_stub)
    g.add_node("discovery_agent", discovery_node)
    g.add_node("human_review_2", _human_review_stub)
    g.add_node("architecture_agent", architecture_node)
    g.add_node("human_review_3", _human_review_stub)
    g.add_node("sprint_agent", sprint_node)
    g.add_node("human_review_4", _human_review_stub)
    g.add_node("change_propagation", _change_propagation)

    # ---- edges ----
    g.add_edge(START, "document_ingestion")
    g.add_edge("document_ingestion", "analyser_agent")
    g.add_edge("analyser_agent", "human_review_1")
    g.add_edge("human_review_1", "discovery_agent")
    g.add_edge("discovery_agent", "human_review_2")
    g.add_edge("human_review_2", "architecture_agent")
    g.add_edge("architecture_agent", "human_review_3")
    g.add_edge("human_review_3", "sprint_agent")
    g.add_edge("sprint_agent", "human_review_4")
    g.add_edge("human_review_4", END)

    # Compile with interrupts — the product person must approve between every pair.
    return g.compile(
        interrupt_before=[
            "human_review_1",
            "human_review_2",
            "human_review_3",
            "human_review_4",
        ],
    )


# Lazy singleton — call `get_graph()` instead of importing `graph` directly,
# so that import-time failures (e.g. missing LLM keys in tests) surface later.
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
