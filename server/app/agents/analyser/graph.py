from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.analyser.nodes.analyse import analyse_node
from app.agents.analyser.nodes.enrich import enrich_node
from app.agents.analyser.nodes.score import score_node
from app.shared.state_types import AnalyserState


def _route_after_score(state: AnalyserState) -> str:
    """If score is low, go to enrich; else go straight to analyse."""
    return "enrich_node" if state["needs_enrichment"] else "analyse_node"


def build_analyser_subgraph():
    """Build Stage-1 subgraph with score -> enrich? -> analyse flow."""
    graph = StateGraph(AnalyserState)

    graph.add_node("score_node", score_node)
    graph.add_node("enrich_node", enrich_node)
    graph.add_node("analyse_node", analyse_node)

    graph.add_edge(START, "score_node")
    graph.add_conditional_edges(
        "score_node",
        _route_after_score,
        {"enrich_node": "enrich_node", "analyse_node": "analyse_node"},
    )
    graph.add_edge("enrich_node", "analyse_node")
    graph.add_edge("analyse_node", END)

    return graph.compile()
