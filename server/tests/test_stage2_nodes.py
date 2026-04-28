from __future__ import annotations

from app.agents.discovery.nodes.finalize_doc import finalize_doc_node
from app.agents.discovery.nodes.generate_question import generate_question_node
from app.agents.discovery.nodes.prioritize import prioritize_questions_node
from app.agents.discovery.nodes.process_answer import process_answer_node


def _discovery_state() -> dict:
    return {
        "project_id": "p1",
        "version": 1,
        "working_chunk_ids": [],
        "analyser_output": {
            "executive_summary": "Summary",
            "project_overview": {"objective": "obj", "scope": "scope", "out_of_scope": "oos"},
            "functional_requirements": [],
            "risks": [],
            "recommended_team": {"roles": [], "size": 3, "rationale": ""},
            "open_questions": [
                {
                    "question_id": "Q-1",
                    "question": "Clarify timeline?",
                    "priority": "high",
                    "blocked_decisions": ["Release plan"],
                }
            ],
            "completeness_score": {
                "functional_requirements": 1.0,
                "business_logic": 1.0,
                "existing_system": 1.0,
                "target_audience": 1.0,
                "architecture_context": 1.0,
                "nfrs": 1.0,
                "timeline_budget": 0.3,
                "visual_assets": 1.0,
                "weighted_total": 8.0,
                "per_criterion_reasoning": {},
            },
            "assumptions_made": [],
        },
        "qa_history": [],
        "current_question": None,
        "questions_asked_count": 0,
        "discovery_terminated": False,
        "final_doc_markdown": None,
        "delta_changes": [],
        "streaming_events": [],
        "llm_config": {},
    }


def test_stage2_question_answer_and_finalize() -> None:
    state = _discovery_state()

    state.update(prioritize_questions_node(state))
    state.update(generate_question_node(state))
    assert state["current_question"] is not None

    state["current_question"]["answer"] = "Timeline will be phased over 3 sprints"
    state["current_question"]["status"] = "answered"

    state.update(process_answer_node(state))
    assert len(state["qa_history"]) == 1

    state.update(finalize_doc_node(state))
    assert "Business Requirements Analysis" in state["final_doc_markdown"]
