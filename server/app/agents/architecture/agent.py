"""
app.agents.architecture.agent
=============================
STAGE 3 — Architecture Agent.

Generates 5 diagrams (BRD §4.4):
    * System Architecture        (PlantUML)
    * Data Flow Diagram          (Mermaid flowchart)
    * User Flow                  (Mermaid sequence / state)
    * Entity Relationship        (PlantUML)
    * Deployment Architecture    (PlantUML)

Inputs:  analyser_output  (post-Discovery)
Outputs: architecture_output = {mermaid: [...], plantuml: [...]}
"""
from __future__ import annotations

from typing import Any

from app.agents.architecture import prompts, tools  # noqa: F401
from app.agents.llm_factory import build_llm
from app.agents.state import GraphState
from app.schemas.architecture import ArchitectureOut

AGENT_ID = "architecture"


async def architecture_node(state: GraphState) -> dict[str, Any]:
    llm = build_llm(AGENT_ID, state)  # noqa: F841
    analyser = state.get("analyser_output")

    # TODO:
    #   * call tools.generate_mermaid_dfd(analyser, llm)
    #   * call tools.generate_mermaid_userflow(analyser, llm)
    #   * call tools.generate_plantuml_system(analyser, llm)
    #   * call tools.generate_plantuml_er(analyser, llm)
    #   * call tools.generate_plantuml_deployment(analyser, llm)
    #   * validate each DSL via services.diagram_service.validate_mermaid / validate_plantuml
    #   * the frontend renders both Mermaid and PlantUML client-side (no server rendering)

    result = ArchitectureOut(mermaid=[], plantuml=[])
    return {"architecture_output": result, "current_stage": "architecture"}
