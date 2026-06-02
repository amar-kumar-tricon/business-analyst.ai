import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * AnalyserPage — Stage 1 live progress + result view.
 *
 * Three states it can be in:
 *   - isRunning + score=null     → live progress feed (Stage 1 + 2 in flight)
 *   - score set + currentQuestion → "Continue to Discovery"
 *   - score set + finalDocReady   → "Review & Approve"
 *   - runError                    → red error banner
 *
 * Owns the WebSocket subscription so the user sees node-by-node progress as
 * each LLM/RAG/parser step completes.
 */
import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { openProjectStream } from "../api/ws";
import { formatEventSummary } from "../lib/events";
import { useAppStore } from "../store/useAppStore";
const CRITERION_LABELS = {
    functional_requirements: "Functional Requirements",
    business_logic: "Business Logic",
    existing_system: "Existing System",
    target_audience: "Target Audience",
    architecture_context: "Architecture",
    nfrs: "NFRs",
    timeline_budget: "Timeline / Budget",
    visual_assets: "Visual Assets",
};
function ScoreCard({ score }) {
    const total = score.weighted_total;
    const colour = total >= 7 ? "text-emerald-500" : total >= 5 ? "text-amber-500" : "text-destructive";
    return (_jsxs("div", { className: "rounded-lg border border-border bg-card p-5", children: [_jsx("h3", { className: "mb-3 text-sm font-medium text-muted-foreground", children: "Completeness Score" }), _jsxs("div", { className: `text-4xl font-bold ${colour}`, children: [total.toFixed(1), " ", _jsx("span", { className: "text-xl text-muted-foreground", children: "/ 10" })] }), _jsx("ul", { className: "mt-4 grid grid-cols-2 gap-x-4 gap-y-1 text-xs", children: Object.entries(CRITERION_LABELS).map(([k, label]) => (_jsxs("li", { className: "flex justify-between", children: [_jsx("span", { className: "text-muted-foreground", children: label }), _jsx("span", { children: score[k].toFixed(2) })] }, k))) })] }));
}
export default function AnalyserPage() {
    const { projectId, projectName, score, currentQuestion, finalDocReady, isRunning, runError, events, appendEvent, resetEvents, } = useAppStore();
    const wsRef = useRef(null);
    const eventListRef = useRef(null);
    // Open the project's event stream as long as we have a project id.
    // Backend replays the backlog on connect, then streams live events.
    useEffect(() => {
        if (!projectId)
            return;
        resetEvents();
        const ws = openProjectStream(projectId, (e) => appendEvent(e));
        wsRef.current = ws;
        return () => {
            ws.close();
            wsRef.current = null;
        };
    }, [projectId, appendEvent, resetEvents]);
    // Auto-scroll the live feed to the latest event.
    useEffect(() => {
        if (eventListRef.current) {
            eventListRef.current.scrollTop = eventListRef.current.scrollHeight;
        }
    }, [events.length]);
    if (!projectId) {
        return (_jsxs("div", { className: "rounded-md border border-border bg-card p-6 text-sm", children: ["No active project \u2014 start from the", " ", _jsx(Link, { to: "/", className: "text-primary underline", children: "upload page" }), "."] }));
    }
    const showLiveFeed = isRunning || (!score && !runError);
    return (_jsxs("section", { className: "space-y-6", children: [_jsxs("header", { className: "flex items-baseline justify-between gap-4", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-xl font-semibold", children: "Stage 1 \u2014 Analyser" }), _jsx("p", { className: "text-sm text-muted-foreground", children: projectName })] }), _jsxs("div", { className: "flex gap-2", children: [currentQuestion && !isRunning && (_jsx(Link, { to: "/discovery", className: "inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90", children: "Continue to Discovery \u2192" })), !currentQuestion && finalDocReady && !isRunning && (_jsx(Link, { to: "/approve", className: "inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90", children: "Review & Approve \u2192" }))] })] }), runError && (_jsx("div", { className: "rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive", children: runError })), showLiveFeed && (_jsxs("div", { className: "rounded-lg border border-border bg-card p-5", children: [_jsxs("div", { className: "mb-3 flex items-center gap-2", children: [_jsx("span", { className: "inline-block h-2 w-2 animate-pulse rounded-full bg-primary" }), _jsx("h3", { className: "text-sm font-medium", children: isRunning ? "Pipeline running…" : "Connecting…" }), _jsxs("span", { className: "ml-auto text-xs text-muted-foreground", children: [events.length, " events"] })] }), _jsxs("ul", { ref: eventListRef, className: "max-h-72 space-y-0.5 overflow-y-auto rounded border border-border bg-background p-3 font-mono text-xs", children: [events.length === 0 && (_jsx("li", { className: "text-muted-foreground", children: "Waiting for first event\u2026" })), events.map((e, i) => (_jsxs("li", { className: "flex gap-2", children: [_jsx("span", { className: "shrink-0 text-muted-foreground", children: new Date(e.timestamp).toLocaleTimeString() }), _jsx("span", { className: "shrink-0 rounded bg-muted px-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground", children: e.node }), _jsx("span", { children: formatEventSummary(e) })] }, `${e.event_id}-${i}`)))] }), _jsx("p", { className: "mt-3 text-xs text-muted-foreground", children: "Stage 1 typically takes 1\u20133 minutes for a multi-section BRD because of LLM calls. You can leave this tab open; the analyser will continue and auto-update when ready." })] })), score && _jsx(ScoreCard, { score: score }), score && (_jsxs("details", { className: "rounded-lg border border-border bg-card p-5", children: [_jsx("summary", { className: "cursor-pointer text-sm font-medium", children: "Per-criterion reasoning" }), _jsx("ul", { className: "mt-3 space-y-2 text-xs text-muted-foreground", children: Object.entries(score.per_criterion_reasoning ?? {}).map(([k, v]) => (_jsxs("li", { children: [_jsxs("span", { className: "font-medium text-foreground", children: [CRITERION_LABELS[k] ?? k, ":", " "] }), v] }, k))) })] }))] }));
}
