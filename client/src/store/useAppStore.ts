/**
 * Global app store (Zustand). Holds the active project, the latest analysis
 * snapshot, the Stage-2 conversation, and the final document so every page
 * reads from one source of truth.
 */
import { create } from "zustand";
import type {
  AnalyserResult,
  AnswerResponse,
  ApproveResponse,
  BackendEvent,
  QAExchange,
  RunResponse,
  ScoreBreakdown,
} from "../types";

interface AppState {
  projectId: string | null;
  projectName: string;
  score: ScoreBreakdown | null;
  analyser: AnalyserResult | null;
  currentQuestion: QAExchange | null;
  qaHistory: QAExchange[];
  finalDocMarkdown: string | null;
  finalDocReady: boolean;
  events: BackendEvent[];

  setProject: (id: string, name: string) => void;
  applyRun: (r: RunResponse) => void;
  applyAnswer: (r: AnswerResponse, sentQA: QAExchange | null) => void;
  applyApprove: (r: ApproveResponse) => void;
  appendEvent: (e: BackendEvent) => void;
  reset: () => void;
}

const initial = {
  projectId: null,
  projectName: "",
  score: null,
  analyser: null,
  currentQuestion: null,
  qaHistory: [] as QAExchange[],
  finalDocMarkdown: null,
  finalDocReady: false,
  events: [] as BackendEvent[],
};

export const useAppStore = create<AppState>((set) => ({
  ...initial,

  setProject: (id, name) => set({ projectId: id, projectName: name }),

  applyRun: (r) =>
    set({
      score: r.score,
      currentQuestion: r.current_question,
      finalDocMarkdown: r.final_doc_markdown,
      finalDocReady: !!r.final_doc_markdown,
    }),

  applyAnswer: (r, sentQA) =>
    set((s) => ({
      qaHistory: sentQA ? [...s.qaHistory, sentQA] : s.qaHistory,
      currentQuestion: r.current_question,
      finalDocMarkdown: r.final_doc_markdown,
      finalDocReady: !!r.final_doc_markdown,
    })),

  applyApprove: (_r) => set({ finalDocReady: true }),

  appendEvent: (e) => set((s) => ({ events: [...s.events, e] })),

  reset: () => set({ ...initial }),
}));
