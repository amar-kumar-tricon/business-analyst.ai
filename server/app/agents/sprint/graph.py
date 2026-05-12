from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.sprint.nodes.plan import sprint_plan_node


def build_sprint_subgraph():
    """Build the sprint planning subgraph with a single plan node."""
    graph = StateGraph(dict)

    graph.add_node("sprint_plan_node", sprint_plan_node)

    graph.add_edge(START, "sprint_plan_node")
    graph.add_edge("sprint_plan_node", END)

    return graph.compile()
