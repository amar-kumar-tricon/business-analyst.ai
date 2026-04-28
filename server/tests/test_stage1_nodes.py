from __future__ import annotations

from app.agents.analyser.nodes.analyse import analyse_node
from app.agents.analyser.nodes.enrich import enrich_node
from app.agents.analyser.nodes.score import score_node


def _analyser_state() -> dict:
    return {
        "project_id": "p1",
        "version": 1,
        "parsed_documents": [
            {
                "file_name": "brd.md",
                "file_type": "text/markdown",
                "s3_key": "uploads/p1/brd.md",
                "sections": [
                    {
                        "file_name": "brd.md",
                        "section_heading": "Requirements",
                        "page": 1,
                        "content_type": "text",
                        "content": "System must support approval workflow and acceptance criteria.",
                        "raw_image_ref": None,
                    }
                ],
            }
        ],
        "working_chunk_ids": [],
        "score": None,
        "needs_enrichment": True,
        "analyser_output": None,
        "delta_changes": [],
        "streaming_events": [],
        "llm_config": {},
    }


def test_stage1_score_enrich_analyse_flow() -> None:
    state = _analyser_state()

    scored = score_node(state)
    assert scored["score"]["weighted_total"] >= 0

    state.update(scored)
    enriched = enrich_node(state)
    state.update(enriched)

    analysed = analyse_node(state)
    assert "analyser_output" in analysed
    assert analysed["analyser_output"]["functional_requirements"]
    assert analysed["analyser_output"]["completeness_score"]["weighted_total"] >= 0
