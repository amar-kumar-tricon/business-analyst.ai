"""
app.agents.state
================
The single source of truth passed between LangGraph nodes.

⚠️  The structure of GraphState is a PUBLIC CONTRACT — every agent node reads
and writes keys defined here. If you need a new field:
    1. add it to GraphState below with a clear comment
    2. update the agent(s) that will read / write it
    3. update `app.agents.graph` if the new field affects routing
"""
from __future__ import annotations

from typing import Literal, TypedDict

from app.schemas.analyser import AnalyserResult
from app.schemas.architecture import ArchitectureOut
from app.schemas.discovery import QAExchange
from app.schemas.sprint import SprintPlanOut


class DocumentChunk(TypedDict):
    document_id: str
    chunk_index: int
    text: str


class ChangeEventLog(TypedDict):
    source_stage: str
    description: str
    reprocessed_stages: list[str]


class LLMConfigInState(TypedDict):
    provider: str
    model_name: str
    temperature: float
    max_tokens: int


StageName = Literal["upload", "analyse", "discovery", "architecture", "sprint", "finalized"]


class GraphState(TypedDict, total=False):
    # ---- identifiers ----
    project_id: str
    version: int

    # ---- inputs ----
    uploaded_documents: list[DocumentChunk]
    additional_context: str

    # ---- stage outputs (populated as the pipeline runs) ----
    analyser_output: AnalyserResult | None
    discovery_qa: list[QAExchange]
    open_questions: list[str]
    architecture_output: ArchitectureOut | None
    sprint_plan: SprintPlanOut | None

    # ---- progress & control ----
    current_stage: StageName
    approval_status: dict[str, bool]  # {"analyse": True, "discovery": False, ...}
    llm_config: dict[str, LLMConfigInState]  # keyed by agent id
    change_log: list[ChangeEventLog]
