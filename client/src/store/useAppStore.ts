/**
 * Global app store (Zustand). Holds the active project, the latest analysis
 * snapshot, the Stage-2 conversation, the final document, and async-run flags
 * so every page reads from one source of truth.
 */
import {create} from 'zustand';

import type {
    AnalyserResult,
    AnswerResponse,
    ApproveResponse,
    ArchitectureOutput,
    ArchitectureResponse,
    BackendEvent,
    QAExchange,
    RunResponse,
    ScoreBreakdown,
} from '../types';

interface AppState {
    projectId: string | null;
    projectName: string;
    score: ScoreBreakdown | null;
    analyser: AnalyserResult | null;
    currentQuestion: QAExchange | null;
    qaHistory: QAExchange[];
    finalDocMarkdown: string | null;
    finalDocReady: boolean;
    architectureOutput: ArchitectureOutput | null;
    events: BackendEvent[];

    // Async-run flags
    isRunning: boolean;
    runError: string | null;

    setProject: (id: string, name: string) => void;
    setRunning: (running: boolean) => void;
    setRunError: (err: string | null) => void;
    applyRun: (r: RunResponse) => void;
    applyAnswer: (r: AnswerResponse, sentQA: QAExchange | null) => void;
    applyApprove: (r: ApproveResponse) => void;
    applyArchitecture: (r: ArchitectureResponse) => void;
    appendEvent: (e: BackendEvent) => void;
    resetEvents: () => void;
    reset: () => void;
}

const initial = {
    projectId: null,
    projectName: '',
    score: null,
    analyser: null,
    currentQuestion: null,
    qaHistory: [] as QAExchange[],
    finalDocMarkdown: null,
    finalDocReady: false,
    architectureOutput: null,
    events: [] as BackendEvent[],
    isRunning: false,
    runError: null as string | null,
};

export const useAppStore = create<AppState>((set) => ({
    ...initial,

    setProject: (id, name) => set({projectId: id, projectName: name}),
    setRunning: (running) => set({isRunning: running}),
    setRunError: (err) => set({runError: err}),

    applyRun: (r) =>
        set({
            score: r.score,
            currentQuestion: r.current_question,
            finalDocMarkdown: r.final_doc_markdown,
            finalDocReady: !!r.final_doc_markdown,
            isRunning: false,
            runError: null,
        }),

    applyAnswer: (r, sentQA) =>
        set((s) => ({
            qaHistory: sentQA ? [...s.qaHistory, sentQA] : s.qaHistory,
            currentQuestion: r.current_question,
            finalDocMarkdown: r.final_doc_markdown,
            finalDocReady: !!r.final_doc_markdown,
            isRunning: false,
            runError: null,
        })),

    applyApprove: (_r) => set({finalDocReady: true, isRunning: false}),

    applyArchitecture: (r) =>
        set({
            architectureOutput: r.architecture_output,
            isRunning: false,
            runError: null,
        }),

    appendEvent: (e) => set((s) => ({events: [...s.events, e]})),
    resetEvents: () => set({events: []}),

    reset: () => set({...initial}),
}));
