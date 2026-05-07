from __future__ import annotations

import logging

from app.shared.state_types import DiscoveryState


log = logging.getLogger(__name__)


def await_answer_node(state: DiscoveryState) -> dict:
    """Pure no-op interrupt placeholder.

    The graph is compiled with interrupt_before=["await_answer_node"],
    so execution STOPS before this function ever runs.

    When the user calls POST /api/projects/{id}/discovery/answer, the
    resume handler injects the answer into current_question via
    Command(resume={...}), then this node runs trivially and passes
    control to process_answer_node.
    """
    qid = (state.get("current_question") or {}).get("question_id")
    log.info("[await_answer] passthrough qid=%s", qid)
    return {}
