"""
Sprint Agent subgraph (Stage 4).
Single-node graph: generate_plan_node → END.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.sprint.nodes.generate_plan import generate_plan_node
from app.shared.state_types import SprintState


def build_sprint_subgraph():
    """Build the Sprint Planning subgraph."""
    graph = StateGraph(SprintState)

    graph.add_node("generate_plan_node", generate_plan_node)

    graph.add_edge(START, "generate_plan_node")
    graph.add_edge("generate_plan_node", END)

    return graph.compile()

