from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.discovery.nodes.await_answer import await_answer_node
from app.agents.discovery.nodes.finalize_doc import finalize_doc_node
from app.agents.discovery.nodes.generate_question import generate_question_node
from app.agents.discovery.nodes.prioritize import prioritize_questions_node
from app.agents.discovery.nodes.process_answer import process_answer_node
from app.shared.state_types import DiscoveryState


def _route_after_process(state: DiscoveryState) -> str:
    """Decide: loop for another question OR go to finalize.

    Termination conditions (any one is enough):
    1. User clicked "I'm done"  → discovery_terminated is True
    2. Hard cap reached         → questions_asked_count >= 10
    3. LLM signalled no more    → current_question is None
    4. All questions answered   → no unasked open questions left
    """
    if state["discovery_terminated"]:
        return "finalize_doc_node"

    if state["questions_asked_count"] >= 10:
        return "finalize_doc_node"

    if state.get("current_question") is None:
        return "finalize_doc_node"

    asked_ids = {qa["question_id"] for qa in state["qa_history"]}
    unresolved = [
        q for q in state["analyser_output"]["open_questions"]
        if q["question_id"] not in asked_ids
    ]
    if not unresolved:
        return "finalize_doc_node"

    return "generate_question_node"


def build_discovery_subgraph():
    """Build and compile the Discovery subgraph.

    Key rules:
    - NO checkpointer here. The parent passes its own checkpointer when
      mounting this as a node; adding one here causes state corruption.
    - interrupt_before=["await_answer_node"] pauses the graph BEFORE
      await_answer_node runs, waiting for the user's API call.
    """
    graph = StateGraph(DiscoveryState)

    graph.add_node("prioritize_questions_node", prioritize_questions_node)
    graph.add_node("generate_question_node", generate_question_node)
    graph.add_node("await_answer_node", await_answer_node)
    graph.add_node("process_answer_node", process_answer_node)
    graph.add_node("finalize_doc_node", finalize_doc_node)

    graph.add_edge(START, "prioritize_questions_node")
    graph.add_edge("prioritize_questions_node", "generate_question_node")
    graph.add_edge("generate_question_node", "await_answer_node")
    graph.add_edge("await_answer_node", "process_answer_node")
    graph.add_conditional_edges(
        "process_answer_node",
        _route_after_process,
        {
            "generate_question_node": "generate_question_node",
            "finalize_doc_node": "finalize_doc_node",
        },
    )
    graph.add_edge("finalize_doc_node", END)

    # Interrupt BEFORE await_answer_node so the graph parks here waiting
    # for the user to call POST /api/projects/{id}/discovery/answer.
    return graph.compile(interrupt_before=["await_answer_node"])
