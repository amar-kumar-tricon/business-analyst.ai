/**
 * Shared TypeScript types — mirror the backend GraphState shapes from
 * server/app/shared/state_types.py. Keep these in sync with the backend.
 */

export type AnswerStatus = 'answered' | 'deferred' | 'na' | 'unknown';
export type Moscow = 'must_have' | 'should_have' | 'good_to_have';
export type Severity = 'high' | 'medium' | 'low';
export type Priority = 'high' | 'medium' | 'low';

export interface ScoreBreakdown {
    functional_requirements: number;
    business_logic: number;
    existing_system: number;
    target_audience: number;
    architecture_context: number;
    nfrs: number;
    timeline_budget: number;
    visual_assets: number;
    weighted_total: number;
    per_criterion_reasoning: Record<string, string>;
}

export interface OpenQuestion {
    question_id: string;
    question: string;
    priority: Priority;
    blocked_decisions: string[];
}

export interface FunctionalRequirement {
    req_id: string;
    description: string;
    moscow: Moscow;
    acceptance_hints: string[];
    source: 'document' | 'enrichment' | 'qa';
    source_ref: string | null;
}

export interface Risk {
    risk_id: string;
    description: string;
    category: 'technical' | 'business' | 'delivery';
    severity: Severity;
    mitigation: string | null;
}

export interface AnalyserResult {
    executive_summary: string;
    project_overview: {
        objective?: string;
        scope?: string;
        out_of_scope?: string;
    };
    functional_requirements: FunctionalRequirement[];
    risks: Risk[];
    recommended_team: {roles?: string[]; size?: number; rationale?: string};
    open_questions: OpenQuestion[];
    completeness_score: ScoreBreakdown;
    assumptions_made: {id: string; text: string; timestamp: string}[];
}

export interface QAExchange {
    question_id: string;
    question: string;
    rationale: string;
    options: string[];
    answer: string | null;
    selected_option_index: number | null;
    status: AnswerStatus;
    timestamp: string;
    triggered_changes: unknown[];
}

export interface BackendEvent {
    event_id: string;
    type: string;
    node: string;
    payload: Record<string, unknown>;
    timestamp: string;
}

/* API response shapes */

export interface CreateProjectResponse {
    project_id: string;
    status: string;
    snapshot: string;
}

export interface UploadFileResponse {
    project_id: string;
    file_name: string;
    sections: number;
    storage_key: string;
}

export interface RunResponse {
    project_id: string;
    score: ScoreBreakdown;
    current_question: QAExchange | null;
    final_doc_markdown: string | null;
}

export interface AnswerResponse {
    project_id: string;
    current_question: QAExchange | null;
    qa_history_count: number;
    final_doc_markdown: string | null;
}

export interface ApproveResponse {
    project_id: string;
    status: 'approved';
    final_doc_pdf_s3_key: string;
    final_doc_docx_s3_key: string;
}

/* Architecture (Stage 3) */

export interface DiagramEntry {
    title: string;
    dsl: string;
    explanation: string;
}

export interface ArchitectureOutput {
    mermaid: DiagramEntry[];
    plantuml: DiagramEntry[];
}

export interface ArchitectureResponse {
    project_id: string;
    architecture_output: ArchitectureOutput;
    mermaid_count: number;
    plantuml_count: number;
}
