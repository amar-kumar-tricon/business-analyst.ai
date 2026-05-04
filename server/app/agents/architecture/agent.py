"""
app.agents.architecture.agent
=============================
STAGE 3 — Architecture Agent.

Generates 5 diagrams:
    * Data Flow Diagram          (Mermaid flowchart)
    * User Flow                  (Mermaid sequence)
    * System Architecture        (PlantUML)
    * Entity Relationship        (PlantUML)
    * Deployment Architecture    (PlantUML)

Inputs:  analyser_output  (post-Discovery)
Outputs: architecture_output = {mermaid: [...], plantuml: [...]}
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.agents.architecture.tools import (
    generate_mermaid_dfd,
    generate_mermaid_userflow,
    generate_plantuml_deployment,
    generate_plantuml_er,
    generate_plantuml_system,
)
from app.shared.state_types import GraphState


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def architecture_node(state: GraphState) -> dict[str, Any]:
    """Generate all architecture diagrams from the analyser output."""
    analyser = state.get("analyser_output")
    if not analyser:
        return {
            "architecture_output": {"mermaid": [], "plantuml": []},
            "streaming_events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "type": "architecture_skipped",
                    "node": "architecture_node",
                    "payload": {"reason": "no analyser_output"},
                    "timestamp": _now_iso(),
                }
            ],
        }

    # Generate diagrams (sync — uses llm_gateway which is sync)
    dfd = generate_mermaid_dfd(analyser)
    user_flow = generate_mermaid_userflow(analyser)
    system = generate_plantuml_system(analyser)
    er = generate_plantuml_er(analyser)
    deployment = generate_plantuml_deployment(analyser)

    result = {
        "mermaid": [
            {"title": "Data Flow Diagram", "type": "dfd", "dsl": dfd},
            {"title": "User Flow", "type": "user_flow", "dsl": user_flow},
        ],
        "plantuml": [
            {"title": "System Architecture", "type": "system", "dsl": system},
            {"title": "ER Diagram", "type": "er", "dsl": er},
            {"title": "Deployment Diagram", "type": "deployment", "dsl": deployment},
        ],
    }

    return {
        "architecture_output": result,
        "streaming_events": [
            {
                "event_id": str(uuid.uuid4()),
                "type": "architecture_ready",
                "node": "architecture_node",
                "payload": {
                    "mermaid_count": len(result["mermaid"]),
                    "plantuml_count": len(result["plantuml"]),
                },
                "timestamp": _now_iso(),
            }
        ],
    }
