import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * DiscoveryPage — Stage 2 Q&A loop.
 *
 * Reads `currentQuestion` from the store and renders the question card with
 * its options, free-text fallback, status buttons, and "I'm done" terminator.
 * Each answer round POSTs /discovery/answer; the response either gives a new
 * question or signals completion (final_doc_markdown becomes available).
 */
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { openProjectStream } from "../api/ws";
import { formatEventSummary } from "../lib/events";
import { useAppStore } from "../store/useAppStore";
export default function DiscoveryPage() {
    const { projectId, projectName, currentQuestion, qaHistory, finalDocReady } = useAppStore();
    const applyAnswer = useAppStore((s) => s.applyAnswer);
    const nav = useNavigate();
    const [selectedIdx, setSelectedIdx] = useState(null);
    const [freeText, setFreeText] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);
    const [liveEvents, setLiveEvents] = useState([]);
    const wsRef = useRef(null);
    useEffect(() => {
        return () => {
            wsRef.current?.close();
            wsRef.current = null;
        };
    }, []);
    if (!projectId) {
        return (_jsxs("div", { className: "rounded-md border border-border bg-card p-6 text-sm", children: ["No active project \u2014 start from the ", _jsx(Link, { to: "/", className: "text-primary underline", children: "upload page" }), "."] }));
    }
    if (!currentQuestion && finalDocReady) {
        return (_jsxs("div", { className: "rounded-md border border-border bg-card p-6 text-sm", children: ["Discovery complete. ", _jsx(Link, { to: "/approve", className: "text-primary underline", children: "Review & approve \u2192" })] }));
    }
    if (!currentQuestion) {
        return _jsx("p", { className: "text-sm text-muted-foreground", children: "No question pending." });
    }
    async function submit(status, terminate) {
        if (!projectId || !currentQuestion)
            return;
        setError(null);
        let answerText = null;
        if (status === "answered") {
            if (selectedIdx !== null) {
                answerText = currentQuestion.options[selectedIdx];
            }
            else if (freeText.trim()) {
                answerText = freeText.trim();
            }
            else {
                return setError("Pick an option or type a free-text answer.");
            }
        }
        setBusy(true);
        setLiveEvents([]);
        wsRef.current?.close();
        wsRef.current = openProjectStream(projectId, (e) => {
            setLiveEvents((prev) => [...prev, formatEventSummary(e)]);
        });
        const sentQA = {
            ...currentQuestion,
            answer: answerText,
            status,
            selected_option_index: selectedIdx,
        };
        try {
            const r = await projectsApi.answer(projectId, {
                answer: answerText,
                status,
                selected_option_index: selectedIdx,
                terminate,
            });
            applyAnswer(r, sentQA);
            setSelectedIdx(null);
            setFreeText("");
            if (!r.current_question || terminate)
                nav("/approve");
        }
        catch (e) {
            setError(e?.response?.data?.detail ?? e.message ?? "Submit failed.");
        }
        finally {
            wsRef.current?.close();
            wsRef.current = null;
            setBusy(false);
        }
    }
    return (_jsxs("section", { className: "grid gap-6 md:grid-cols-3", children: [_jsxs("div", { className: "md:col-span-2 space-y-4", children: [_jsxs("header", { children: [_jsx("h2", { className: "text-xl font-semibold", children: "Stage 2 \u2014 Discovery" }), _jsx("p", { className: "text-sm text-muted-foreground", children: projectName })] }), _jsxs("article", { className: "rounded-lg border border-border bg-card p-5", children: [_jsxs("p", { className: "mb-1 text-xs uppercase tracking-wide text-muted-foreground", children: ["Question ", qaHistory.length + 1, " \u00B7 ", currentQuestion.question_id] }), _jsx("h3", { className: "text-lg font-semibold leading-snug", children: currentQuestion.question }), currentQuestion.rationale && (_jsxs("p", { className: "mt-2 text-sm text-muted-foreground", children: [_jsx("span", { className: "font-medium text-foreground", children: "Why this matters: " }), currentQuestion.rationale] })), _jsx("div", { className: "mt-4 space-y-2", children: currentQuestion.options.map((opt, i) => (_jsxs("label", { className: `flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm ${selectedIdx === i
                                        ? "border-primary bg-primary/10"
                                        : "border-border hover:bg-accent"}`, children: [_jsx("input", { type: "radio", name: "opt", className: "mt-1", checked: selectedIdx === i, onChange: () => {
                                                setSelectedIdx(i);
                                                setFreeText("");
                                            } }), _jsx("span", { children: opt })] }, i))) }), _jsxs("div", { className: "mt-4 space-y-2", children: [_jsx("label", { className: "text-xs font-medium text-muted-foreground", children: "Or write your own answer" }), _jsx("textarea", { rows: 3, value: freeText, onChange: (e) => {
                                            setFreeText(e.target.value);
                                            if (e.target.value)
                                                setSelectedIdx(null);
                                        }, placeholder: "Free-text answer (overrides any selected option)", className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" })] }), error && (_jsx("div", { className: "mt-3 rounded-md border border-destructive/50 bg-destructive/10 p-2 text-sm text-destructive", children: error })), busy && (_jsxs("div", { className: "mt-4 rounded-md border border-border bg-muted/40 p-3", children: [_jsxs("p", { className: "mb-2 flex items-center gap-2 text-xs font-medium", children: [_jsx("span", { className: "inline-block h-2 w-2 animate-pulse rounded-full bg-primary" }), "Processing answer (LLM calls in progress)\u2026"] }), liveEvents.length > 0 ? (_jsx("ul", { className: "max-h-40 space-y-0.5 overflow-y-auto font-mono text-xs text-muted-foreground", children: liveEvents.map((line, i) => (_jsxs("li", { children: ["\u00B7 ", line] }, i))) })) : (_jsx("p", { className: "text-xs text-muted-foreground", children: "Waiting for first event\u2026" }))] })), _jsxs("div", { className: "mt-5 flex flex-wrap gap-2", children: [_jsx("button", { disabled: busy, onClick: () => submit("answered", false), className: "inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50", children: "Submit" }), _jsx("button", { disabled: busy, onClick: () => submit("deferred", false), className: "inline-flex h-9 items-center rounded-md border border-border px-4 text-sm font-medium hover:bg-accent disabled:opacity-50", children: "Defer" }), _jsx("button", { disabled: busy, onClick: () => submit("na", false), className: "inline-flex h-9 items-center rounded-md border border-border px-4 text-sm font-medium hover:bg-accent disabled:opacity-50", children: "Not Applicable" }), _jsx("button", { disabled: busy, onClick: () => submit("answered", true), className: "ml-auto inline-flex h-9 items-center rounded-md border border-destructive/40 px-4 text-sm font-medium text-destructive hover:bg-destructive/10 disabled:opacity-50", children: "I'm done \u2014 finish discovery" })] })] })] }), _jsxs("aside", { className: "md:col-span-1", children: [_jsxs("h3", { className: "mb-2 text-sm font-medium text-muted-foreground", children: ["Q&A history (", qaHistory.length, ")"] }), qaHistory.length === 0 && (_jsx("p", { className: "text-xs text-muted-foreground", children: "No previous questions yet." })), _jsx("ul", { className: "space-y-3", children: qaHistory.map((qa) => (_jsxs("li", { className: "rounded-md border border-border bg-card p-3 text-xs", children: [_jsx("p", { className: "font-medium leading-snug", children: qa.question }), _jsxs("p", { className: "mt-1 text-muted-foreground", children: [qa.status === "answered" && (qa.answer || "(empty)"), qa.status === "deferred" && "[Deferred]", qa.status === "na" && "[Not Applicable]", qa.status === "unknown" && "[Unknown]"] })] }, qa.question_id))) })] })] }));
}
