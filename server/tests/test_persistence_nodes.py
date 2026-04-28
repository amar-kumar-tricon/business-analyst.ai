from __future__ import annotations

from app.agents.graph import artifact_export_node, approved_rag_index_node, raw_rag_index_node


def _graph_state() -> dict:
    return {
        "project_id": "p2",
        "version": 1,
        "thread_id": "p2",
        "raw_files": ["doc.txt"],
        "additional_context": "",
        "parsed_documents": [
            {
                "file_name": "doc.txt",
                "file_type": "text/plain",
                "s3_key": "uploads/p2/doc.txt",
                "sections": [
                    {
                        "file_name": "doc.txt",
                        "section_heading": "Intro",
                        "page": 1,
                        "content_type": "text",
                        "content": "System must support exports.",
                        "raw_image_ref": None,
                    }
                ],
            }
        ],
        "working_chunk_ids": [],
        "score": None,
        "needs_enrichment": False,
        "analyser_output": {
            "executive_summary": "summary",
            "project_overview": {},
            "functional_requirements": [
                {
                    "req_id": "FR-1",
                    "description": "Export PDF",
                    "moscow": "must_have",
                    "acceptance_hints": [],
                    "source": "document",
                    "source_ref": None,
                }
            ],
            "risks": [],
            "recommended_team": {},
            "open_questions": [],
            "completeness_score": {
                "functional_requirements": 1,
                "business_logic": 1,
                "existing_system": 1,
                "target_audience": 1,
                "architecture_context": 1,
                "nfrs": 1,
                "timeline_budget": 1,
                "visual_assets": 1,
                "weighted_total": 10,
                "per_criterion_reasoning": {},
            },
            "assumptions_made": [],
        },
        "qa_history": [],
        "current_question": None,
        "questions_asked_count": 0,
        "discovery_terminated": False,
        "final_doc_markdown": "# Final",
        "final_doc_pdf_s3_key": None,
        "final_doc_docx_s3_key": None,
        "review_1_status": "approved",
        "review_2_status": "approved",
        "user_edits_payload": None,
        "delta_changes": [],
        "streaming_events": [],
        "llm_config": {},
    }


def test_index_and_artifact_nodes() -> None:
    state = _graph_state()
    state.update(raw_rag_index_node(state))
    assert state["working_chunk_ids"]

    state.update(approved_rag_index_node(state))
    state.update(artifact_export_node(state))
    assert state["final_doc_pdf_s3_key"]
    assert state["final_doc_docx_s3_key"]
