from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.analyser import build_analyser_subgraph
from app.agents.discovery import build_discovery_subgraph
from app.shared.state_types import GraphState


def ingest_node(state: GraphState) -> dict:
    """Normalize ingest payload into parent state.

    Placeholder for Stage 6+: parse uploaded files and map to ParsedDocument.
    """
    _ = state
    return {}


def raw_rag_index_node(state: GraphState) -> dict:
    """Index raw parsed chunks before analysis.

    Placeholder for Stage 6+: create embeddings and store chunk IDs.
    """
    _ = state
    return {}


def apply_review_1_edits_node(state: GraphState) -> dict:
    """Apply human edits after analyser output review.

    Placeholder for Stage 6+: patch analyser_output and append DeltaChange rows.
    """
    _ = state
    return {}


def route_review_2_node(state: GraphState) -> dict:
    """Interrupt gate before deciding discovery loop vs approval path."""
    _ = state
    return {}


def apply_review_2_edits_node(state: GraphState) -> dict:
    """Apply final human edits on generated markdown.

    Placeholder for Stage 8+: patch final_doc_markdown + audit deltas.
    """
    _ = state
    return {}


def approved_rag_index_node(state: GraphState) -> dict:
    """Index approved final analysis artifacts for retrieval.

    Placeholder for Stage 10.
    """
    _ = state
    return {}


def artifact_export_node(state: GraphState) -> dict:
    """Export markdown to PDF/DOCX and persist object keys.

    Placeholder for Stage 10: set final_doc_pdf_s3_key/final_doc_docx_s3_key.
    """
    _ = state
    return {}


def _route_after_analyser(state: GraphState) -> str:
    """Route based on first human review decision."""
    return "discovery_stage_node" if state["review_1_status"] == "approved" else "apply_review_1_edits_node"


def _route_after_review_2(state: GraphState) -> str:
    """Route after second human review checkpoint."""
    if state["review_2_status"] == "more_questions":
        return "discovery_stage_node"
    if state["review_2_status"] == "approved":
        return "approved_rag_index_node"
    return "apply_review_2_edits_node"


def build_parent_graph():
    analyser_subgraph = build_analyser_subgraph()
    discovery_subgraph = build_discovery_subgraph()

    graph = StateGraph(GraphState)

    graph.add_node("ingest_node", ingest_node)
    graph.add_node("raw_rag_index_node", raw_rag_index_node)
    graph.add_node("analyser_stage_node", analyser_subgraph)
    graph.add_node("apply_review_1_edits_node", apply_review_1_edits_node)
    graph.add_node("discovery_stage_node", discovery_subgraph)
    graph.add_node("route_review_2_node", route_review_2_node)
    graph.add_node("apply_review_2_edits_node", apply_review_2_edits_node)
    graph.add_node("approved_rag_index_node", approved_rag_index_node)
    graph.add_node("artifact_export_node", artifact_export_node)

    graph.add_edge(START, "ingest_node")
    graph.add_edge("ingest_node", "raw_rag_index_node")
    graph.add_edge("raw_rag_index_node", "analyser_stage_node")
    graph.add_conditional_edges(
        "analyser_stage_node",
        _route_after_analyser,
        {
            "apply_review_1_edits_node": "apply_review_1_edits_node",
            "discovery_stage_node": "discovery_stage_node",
        },
    )
    graph.add_edge("apply_review_1_edits_node", "discovery_stage_node")
    graph.add_edge("discovery_stage_node", "route_review_2_node")
    graph.add_conditional_edges(
        "route_review_2_node",
        _route_after_review_2,
        {
            "apply_review_2_edits_node": "apply_review_2_edits_node",
            "discovery_stage_node": "discovery_stage_node",
            "approved_rag_index_node": "approved_rag_index_node",
        },
    )
    graph.add_edge("apply_review_2_edits_node", "approved_rag_index_node")
    graph.add_edge("approved_rag_index_node", "artifact_export_node")
    graph.add_edge("artifact_export_node", END)

    return graph.compile(
        interrupt_before=["apply_review_1_edits_node", "route_review_2_node"]
    )

def get_graph():
    return build_parent_graph()
