from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Literal

from app.agents.analyser.nodes.analyse import analyse_node
from app.agents.analyser.nodes.enrich import enrich_node
from app.agents.analyser.nodes.score import score_node
from app.agents.architecture.agent import architecture_node
from app.agents.discovery.nodes.finalize_doc import finalize_doc_node
from app.agents.discovery.nodes.generate_question import generate_question_node
from app.agents.discovery.nodes.prioritize import prioritize_questions_node
from app.agents.discovery.nodes.process_answer import process_answer_node
from app.agents.graph import artifact_export_node, approved_rag_index_node, ingest_node, raw_rag_index_node
from app.shared.event_bus import event_bus
from app.shared.state_types import GraphState, ParsedDocument, ParsedSection, StreamEvent


_PROJECT_STATES: dict[str, GraphState] = {}


def _now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _emit(state: GraphState, node: str, event_type: str, payload: dict) -> None:
    """Create one stream event and publish it to listeners."""
    event: StreamEvent = {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "node": node,
        "payload": payload,
        "timestamp": _now_iso(),
    }
    state["streaming_events"] = state.get("streaming_events", []) + [event]
    event_bus.publish(state["project_id"], event)


def init_project_state(project_id: str, name: str, additional_context: str = "") -> GraphState:
    """Create initial in-memory state for a new project."""
    seed_section: ParsedSection = {
        "file_name": f"{name}.txt",
        "section_heading": "Project Context",
        "page": 1,
        "content_type": "text",
        "content": additional_context or "No additional context provided.",
        "raw_image_ref": None,
    }
    parsed_doc: ParsedDocument = {
        "file_name": f"{name}.txt",
        "file_type": "text/plain",
        "s3_key": f"uploads/{project_id}/{name}.txt",
        "sections": [seed_section],
    }

    state: GraphState = {
        "project_id": project_id,
        "version": 1,
        "thread_id": project_id,
        "raw_files": [f"{name}.txt"],
        "additional_context": additional_context,
        "parsed_documents": [parsed_doc],
        "working_chunk_ids": [],
        "score": None,
        "needs_enrichment": True,
        "analyser_output": None,
        "qa_history": [],
        "current_question": None,
        "questions_asked_count": 0,
        "discovery_terminated": False,
        "final_doc_markdown": None,
        "final_doc_pdf_s3_key": None,
        "final_doc_docx_s3_key": None,
        "architecture_output": None,
        "review_1_status": "approved",
        "review_2_status": "pending",
        "user_edits_payload": None,
        "delta_changes": [],
        "streaming_events": [],
        "llm_config": {},
    }

    _PROJECT_STATES[project_id] = state
    _emit(state, "bootstrap", "project_created", {"name": name})
    return deepcopy(state)


def get_project_state(project_id: str) -> GraphState | None:
    """Read project state from in-memory runtime store."""
    state = _PROJECT_STATES.get(project_id)
    return deepcopy(state) if state else None


def _save(state: GraphState) -> GraphState:
    """Persist updated state in memory and return a safe copy."""
    _PROJECT_STATES[state["project_id"]] = state
    return deepcopy(state)


def append_parsed_document(project_id: str, parsed_document: ParsedDocument, raw_file_name: str) -> GraphState:
    """Add one parsed document into runtime state.

    This is used by upload endpoints before running the graph flow.
    """
    state = deepcopy(_PROJECT_STATES[project_id])
    state["parsed_documents"] = state.get("parsed_documents", []) + [parsed_document]
    state["raw_files"] = state.get("raw_files", []) + [raw_file_name]
    _emit(state, "upload", "file_parsed", {"file_name": raw_file_name})
    return _save(state)


def run_stage1_and_discovery(project_id: str) -> GraphState:
    """Run Stage-1 and Stage-2 until a question is ready or final doc is ready."""
    state = deepcopy(_PROJECT_STATES[project_id])

    state.update(ingest_node(state))
    _emit(state, "ingest_node", "node_completed", {})

    state.update(raw_rag_index_node(state))
    _emit(state, "raw_rag_index_node", "node_completed", {"chunks": len(state["working_chunk_ids"])})

    state.update(score_node(state))
    _emit(state, "score_node", "score_ready", {"weighted_total": state["score"]["weighted_total"]})

    if state["needs_enrichment"]:
        state.update(enrich_node(state))
        _emit(state, "enrich_node", "node_completed", {})

    state.update(analyse_node(state))
    _emit(state, "analyse_node", "analysis_ready", {"open_questions": len(state["analyser_output"]["open_questions"])})

    state.update(prioritize_questions_node(state))
    state.update(generate_question_node(state))

    if state.get("current_question") is None:
        state.update(finalize_doc_node(state))
        _emit(state, "finalize_doc_node", "document_ready", {})
    else:
        _emit(
            state,
            "generate_question_node",
            "question_ready",
            {"question_id": state["current_question"]["question_id"]},
        )

    return _save(state)


def resume_discovery(
    project_id: str,
    answer: str | None,
    status: Literal["answered", "deferred", "na", "unknown"],
    selected_option_index: int | None,
    terminate: bool,
) -> GraphState:
    """Resume Stage-2 after user answers a discovery question."""
    state = deepcopy(_PROJECT_STATES[project_id])

    if state.get("current_question") is not None:
        state["current_question"]["answer"] = answer
        state["current_question"]["status"] = status
        state["current_question"]["selected_option_index"] = selected_option_index

    if terminate:
        state["discovery_terminated"] = True

    state.update(process_answer_node(state))
    _emit(state, "process_answer_node", "answer_processed", {"status": status})

    if not state["discovery_terminated"]:
        state.update(prioritize_questions_node(state))
        state.update(generate_question_node(state))

    if state.get("current_question") is None or state["discovery_terminated"]:
        state.update(finalize_doc_node(state))
        _emit(state, "finalize_doc_node", "document_ready", {})
    else:
        _emit(
            state,
            "generate_question_node",
            "question_ready",
            {"question_id": state["current_question"]["question_id"]},
        )

    return _save(state)


def run_architecture(project_id: str) -> GraphState:
    """Run Stage-3 architecture diagram generation."""
    state = deepcopy(_PROJECT_STATES[project_id])

    state.update(architecture_node(state))
    _emit(
        state,
        "architecture_node",
        "architecture_ready",
        {
            "mermaid_count": len(state.get("architecture_output", {}).get("mermaid", [])),
            "plantuml_count": len(state.get("architecture_output", {}).get("plantuml", [])),
        },
    )

    return _save(state)


def approve_and_export(project_id: str, user_edits_payload: dict | None = None) -> GraphState:
    """Finalize approved output, build approved index, and export artifacts."""
    state = deepcopy(_PROJECT_STATES[project_id])
    state["review_2_status"] = "approved"
    state["user_edits_payload"] = user_edits_payload

    state.update(approved_rag_index_node(state))
    _emit(state, "approved_rag_index_node", "index_ready", {})

    state.update(artifact_export_node(state))
    _emit(
        state,
        "artifact_export_node",
        "artifacts_ready",
        {
            "pdf": state.get("final_doc_pdf_s3_key"),
            "docx": state.get("final_doc_docx_s3_key"),
        },
    )

    return _save(state)
