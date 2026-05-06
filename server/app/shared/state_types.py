from __future__ import annotations

from operator import add
from typing import Annotated, Literal, TypedDict


class ParsedSection(TypedDict):
    file_name: str
    section_heading: str | None
    page: int | None
    content_type: Literal["text", "table", "image_description"]
    content: str
    raw_image_ref: str | None


class ParsedDocument(TypedDict):
    file_name: str
    file_type: str
    s3_key: str
    sections: list[ParsedSection]


class ScoreBreakdown(TypedDict):
    functional_requirements: float
    business_logic: float
    existing_system: float
    target_audience: float
    architecture_context: float
    nfrs: float
    timeline_budget: float
    visual_assets: float
    weighted_total: float
    per_criterion_reasoning: dict[str, str]


class OpenQuestion(TypedDict):
    question_id: str
    question: str
    priority: Literal["high", "medium", "low"]
    blocked_decisions: list[str]


class FunctionalRequirement(TypedDict):
    req_id: str
    description: str
    moscow: Literal["must_have", "should_have", "good_to_have"]
    acceptance_hints: list[str]
    source: Literal["document", "enrichment", "qa"]
    source_ref: str | None


class Risk(TypedDict):
    risk_id: str
    description: str
    category: Literal["technical", "business", "delivery"]
    severity: Literal["high", "medium", "low"]
    mitigation: str | None


class AnalyserResult(TypedDict):
    executive_summary: str
    project_overview: dict
    functional_requirements: list[FunctionalRequirement]
    risks: list[Risk]
    recommended_team: dict
    open_questions: list[OpenQuestion]
    completeness_score: ScoreBreakdown
    assumptions_made: list[dict]


class QAExchange(TypedDict):
    question_id: str
    question: str
    rationale: str
    options: list[str]
    answer: str | None
    selected_option_index: int | None
    status: Literal["answered", "deferred", "na", "unknown"]
    timestamp: str
    triggered_changes: list[dict]


class DeltaChange(TypedDict):
    change_id: str
    source: Literal["enrichment", "qa", "user_edit"]
    source_ref: str
    field_path: str
    old_value: str | None
    new_value: str
    timestamp: str


class StreamEvent(TypedDict):
    event_id: str
    type: str
    node: str
    payload: dict
    timestamp: str


# ──────────────────────────────────────────────
# Stage 3 — Architecture Agent types
# ──────────────────────────────────────────────

class ArchitectureDiagram(TypedDict):
    diagram_id: str
    title: str
    diagram_type: Literal[
        "system_architecture", "data_flow", "user_flow",
        "entity_relationship", "deployment"
    ]
    tool: Literal["mermaid", "plantuml"]
    dsl: str
    description: str


class ArchitectureResult(TypedDict):
    diagrams: list[ArchitectureDiagram]
    tech_stack_notes: str
    generated_at: str
    is_mocked: bool  # True until real Architecture Agent is wired in


# ──────────────────────────────────────────────
# Stage 4 — Sprint Planning Agent types
# ──────────────────────────────────────────────

class SprintStory(TypedDict):
    story_id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    story_points: int
    man_hours: int
    role: str
    moscow: Literal["must_have", "should_have", "good_to_have"]
    sprint_number: int
    is_mvp: bool
    source_req_id: str | None


class SprintData(TypedDict):
    sprint_number: int
    sprint_goal: str
    stories: list[SprintStory]
    total_points: int
    total_hours: int
    start_week: int
    end_week: int


class SprintPlan(TypedDict):
    total_sprints: int
    total_story_points: int
    total_man_hours: int
    mvp_cutoff_sprint: int
    sprint_duration_weeks: int
    team_composition: dict
    tech_stack: dict
    risk_register: list[dict]
    sprints: list[SprintData]
    generated_at: str


class SprintState(TypedDict):
    project_id: str
    version: int
    analyser_output: AnalyserResult
    architecture_output: ArchitectureResult | None
    sprint_plan: SprintPlan | None
    delta_changes: Annotated[list[DeltaChange], add]
    streaming_events: Annotated[list[StreamEvent], add]
    llm_config: dict[str, dict]


class GraphState(TypedDict):
    project_id: str
    version: int
    thread_id: str

    raw_files: list[str]
    additional_context: str

    parsed_documents: list[ParsedDocument]
    working_chunk_ids: list[str]

    score: ScoreBreakdown | None
    needs_enrichment: bool
    analyser_output: AnalyserResult | None

    qa_history: Annotated[list[QAExchange], add]
    current_question: QAExchange | None
    questions_asked_count: int
    discovery_terminated: bool

    final_doc_markdown: str | None
    final_doc_pdf_s3_key: str | None
    final_doc_docx_s3_key: str | None

    architecture_output: ArchitectureResult | None
    sprint_plan: SprintPlan | None

    review_1_status: Literal["pending", "edits_made", "approved"]
    review_2_status: Literal["pending", "edits_made", "more_questions", "approved"]
    review_3_status: Literal["pending", "approved", "regenerate"]
    review_4_status: Literal["pending", "approved"]
    user_edits_payload: dict | None

    delta_changes: Annotated[list[DeltaChange], add]
    streaming_events: Annotated[list[StreamEvent], add]

    llm_config: dict[str, dict]


class AnalyserState(TypedDict):
    project_id: str
    version: int
    parsed_documents: list[ParsedDocument]
    working_chunk_ids: list[str]
    score: ScoreBreakdown | None
    needs_enrichment: bool
    analyser_output: AnalyserResult | None
    delta_changes: Annotated[list[DeltaChange], add]
    streaming_events: Annotated[list[StreamEvent], add]
    llm_config: dict[str, dict]


class DiscoveryState(TypedDict):
    project_id: str
    version: int
    working_chunk_ids: list[str]
    analyser_output: AnalyserResult
    qa_history: Annotated[list[QAExchange], add]
    current_question: QAExchange | None
    questions_asked_count: int
    discovery_terminated: bool
    final_doc_markdown: str | None
    delta_changes: Annotated[list[DeltaChange], add]
    streaming_events: Annotated[list[StreamEvent], add]
    llm_config: dict[str, dict]
