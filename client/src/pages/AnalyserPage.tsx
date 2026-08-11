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
import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';

import { openProjectStream } from '../api/ws';
import { formatEventSummary } from '../lib/events';
import { useAppStore } from '../store/useAppStore';

import type { ScoreBreakdown } from "../types";

const CRITERION_LABELS: Record<string, string> = {
  functional_requirements: "Functional Requirements",
  business_logic: "Business Logic",
  existing_system: "Existing System",
  target_audience: "Target Audience",
  architecture_context: "Architecture",
  nfrs: "NFRs",
  timeline_budget: "Timeline / Budget",
  visual_assets: "Visual Assets",
};

function ScoreCard({ score }: { score: ScoreBreakdown }) {
  const total = score.weighted_total;
  const colour =
    total >= 7 ? "text-emerald-500" : total >= 5 ? "text-amber-500" : "text-destructive";
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground">Completeness Score</h3>
      <div className={`text-4xl font-bold ${colour}`}>
        {total.toFixed(1)} <span className="text-xl text-muted-foreground">/ 10</span>
      </div>
      <ul className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        {Object.entries(CRITERION_LABELS).map(([k, label]) => (
          <li key={k} className="flex justify-between">
            <span className="text-muted-foreground">{label}</span>
            <span>{(score[k as keyof ScoreBreakdown] as number).toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function AnalyserPage() {
  const {
    projectId,
    projectName,
    score,
    currentQuestion,
    finalDocReady,
    isRunning,
    runError,
    events,
    appendEvent,
    resetEvents,
  } = useAppStore();

  const wsRef = useRef<WebSocket | null>(null);
  const eventListRef = useRef<HTMLUListElement | null>(null);

  // Open the project's event stream as long as we have a project id.
  // Backend replays the backlog on connect, then streams live events.
  useEffect(() => {
    if (!projectId) return;
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
    return (
      <div className="rounded-md border border-border bg-card p-6 text-sm">
        No active project — start from the{" "}
        <Link to="/" className="text-primary underline">
          upload page
        </Link>
        .
      </div>
    );
  }

  const showLiveFeed = isRunning || (!score && !runError);

  return (
    <section className="space-y-6">
      <header className="flex items-baseline justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">Stage 1 — Analyser</h2>
          <p className="text-sm text-muted-foreground">{projectName}</p>
        </div>
        <div className="flex gap-2">
          {currentQuestion && !isRunning && (
            <Link
              to="/discovery"
              className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              Continue to Discovery →
            </Link>
          )}
          {!currentQuestion && finalDocReady && !isRunning && (
            <Link
              to="/approve"
              className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              Review & Approve →
            </Link>
          )}
        </div>
      </header>

      {runError && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          {runError}
        </div>
      )}

      {showLiveFeed && (
        <div className="rounded-lg border border-border bg-card p-5">
          <div className="mb-3 flex items-center gap-2">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
            <h3 className="text-sm font-medium">
              {isRunning ? "Pipeline running…" : "Connecting…"}
            </h3>
            <span className="ml-auto text-xs text-muted-foreground">
              {events.length} events
            </span>
          </div>
          <ul
            ref={eventListRef}
            className="max-h-72 space-y-0.5 overflow-y-auto rounded border border-border bg-background p-3 font-mono text-xs"
          >
            {events.length === 0 && (
              <li className="text-muted-foreground">Waiting for first event…</li>
            )}
            {events.map((e, i) => (
              <li key={`${e.event_id}-${i}`} className="flex gap-2">
                <span className="shrink-0 text-muted-foreground">
                  {new Date(e.timestamp).toLocaleTimeString()}
                </span>
                <span className="shrink-0 rounded bg-muted px-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                  {e.node}
                </span>
                <span>{formatEventSummary(e)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">
            Stage 1 typically takes 1–3 minutes for a multi-section BRD because of LLM calls.
            You can leave this tab open; the analyser will continue and auto-update when ready.
          </p>
        </div>
      )}

      {score && <ScoreCard score={score} />}

      {score && (
        <details className="rounded-lg border border-border bg-card p-5">
          <summary className="cursor-pointer text-sm font-medium">
            Per-criterion reasoning
          </summary>
          <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
            {Object.entries(score.per_criterion_reasoning ?? {}).map(([k, v]) => (
              <li key={k}>
                <span className="font-medium text-foreground">
                  {CRITERION_LABELS[k] ?? k}:{" "}
                </span>
                {v}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
