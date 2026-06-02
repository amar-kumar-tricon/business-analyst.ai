/**
 * Global app store (Zustand). Holds the active project, the latest analysis
 * snapshot, the Stage-2 conversation, the final document, sprint plan, and
 * async-run flags so every page reads from one source of truth.
 */
import { create } from "zustand";
const initial = {
    projectId: null,
    projectName: "",
    score: null,
    analyser: null,
    currentQuestion: null,
    qaHistory: [],
    finalDocMarkdown: null,
    finalDocReady: false,
    events: [],
    sprintPlan: null,
    isRunning: false,
    runError: null,
};
export const useAppStore = create((set) => ({
    ...initial,
    setProject: (id, name) => set({ projectId: id, projectName: name }),
    setRunning: (running) => set({ isRunning: running }),
    setRunError: (err) => set({ runError: err }),
    applyRun: (r) => set({
        score: r.score,
        currentQuestion: r.current_question,
        finalDocMarkdown: r.final_doc_markdown,
        finalDocReady: !!r.final_doc_markdown,
        isRunning: false,
        runError: null,
    }),
    applyAnswer: (r, sentQA) => set((s) => ({
        qaHistory: sentQA ? [...s.qaHistory, sentQA] : s.qaHistory,
        currentQuestion: r.current_question,
        finalDocMarkdown: r.final_doc_markdown,
        finalDocReady: !!r.final_doc_markdown,
        isRunning: false,
        runError: null,
    })),
    applyApprove: (_r) => set({ finalDocReady: true, isRunning: false }),
    applySprintPlan: (r) => set({ sprintPlan: r.sprint_plan, isRunning: false, runError: null }),
    appendEvent: (e) => set((s) => ({ events: [...s.events, e] })),
    resetEvents: () => set({ events: [] }),
    reset: () => set({ ...initial }),
}));
