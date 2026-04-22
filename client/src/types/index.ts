/**
 * Shared TypeScript types mirroring backend Pydantic schemas (server/app/schemas).
 * Keep in sync when backend schemas change.
 */

export type StageName =
  | "upload"
  | "analyse"
  | "discovery"
  | "architecture"
  | "sprint"
  | "finalized";

export interface Project {
  id: string;
  name: string;
  current_stage: StageName;
  version: number;
  created_at: string;
}

export interface AnalyserResult {
  executive_summary: string;
  project_overview: { objective: string; scope: string; out_of_scope: string };
  functional_requirements: {
    must_have: string[];
    should_have: string[];
    good_to_have: string[];
  };
  risks: { title: string; severity: "low" | "medium" | "high"; description: string }[];
  recommended_team: { role: string; count: number }[];
  open_questions: string[];
  completeness_score: { total: number; breakdown: Record<string, number> };
}

export interface QAExchange {
  id: string;
  question: string;
  answer?: string;
  status: "pending" | "answered" | "deferred" | "na";
}

export interface ArchitectureResult {
  mermaid: { id: string; title: string; dsl: string }[];
  plantuml: { id: string; title: string; dsl: string; svg?: string }[];
}

export interface SprintPlan {
  total_sprints: number;
  total_story_points: number;
  total_man_hours: number;
  mvp_cutoff_sprint: number;
  sprints: {
    number: number;
    goal: string;
    stories: { id: string; title: string; points: number; role: string; acceptance: string[] }[];
  }[];
  team_composition: { role: string; count: number }[];
}
