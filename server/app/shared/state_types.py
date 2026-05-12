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


class UserStory(TypedDict):
    story_id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    story_points: int
    role: str
    req_id: str


class Sprint(TypedDict):
    sprint_number: int
    sprint_name: str
    goal: str
    features: list[str]
    stories: list[UserStory]
    total_points: int
    man_hours: int
    is_mvp_cutoff: bool


class TeamMember(TypedDict):
    role: str
    count: int
    hours_per_sprint: int


class TechStackItem(TypedDict):
    component: str
    technology: str
    rationale: str


class SprintRisk(TypedDict):
    risk_id: str
    description: str
    category: str
    severity: str
    mitigation: str
    sprint_impacted: int | None


class SprintPlan(TypedDict):
    total_sprints: int
    sprint_duration_weeks: int
    total_story_points: int
    total_man_hours: int
    mvp_cutoff_sprint: int
    team_composition: list[TeamMember]
    technology_stack: list[TechStackItem]
    sprints: list[Sprint]
    risk_register: list[SprintRisk]
    generated_at: str


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

    review_1_status: Literal["pending", "edits_made", "approved"]
    review_2_status: Literal["pending", "edits_made", "more_questions", "approved"]
    user_edits_payload: dict | None

    sprint_plan: SprintPlan | None

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
