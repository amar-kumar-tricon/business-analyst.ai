/**
 * DiscoveryPage — Stage 2 Q&A loop.
 *
 * Reads `currentQuestion` from the store and renders the question card with
 * its options, free-text fallback, status buttons, and "I'm done" terminator.
 * Each answer round POSTs /discovery/answer; the response either gives a new
 * question or signals completion (final_doc_markdown becomes available).
 */
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { projectsApi } from '../api/projects';
import { openProjectStream } from '../api/ws';
import { formatEventSummary } from '../lib/events';
import { useAppStore } from '../store/useAppStore';

import type { AnswerStatus } from "../types";

export default function DiscoveryPage() {
  const { projectId, projectName, currentQuestion, qaHistory, finalDocReady } = useAppStore();
  const applyAnswer = useAppStore((s) => s.applyAnswer);
  const nav = useNavigate();

  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [freeText, setFreeText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [liveEvents, setLiveEvents] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, []);

  if (!projectId) {
    return (
      <div className="rounded-md border border-border bg-card p-6 text-sm">
        No active project — start from the <Link to="/" className="text-primary underline">upload page</Link>.
      </div>
    );
  }

  if (!currentQuestion && finalDocReady) {
    return (
      <div className="rounded-md border border-border bg-card p-6 text-sm">
        Discovery complete. <Link to="/approve" className="text-primary underline">Review & approve →</Link>
      </div>
    );
  }

  if (!currentQuestion) {
    return <p className="text-sm text-muted-foreground">No question pending.</p>;
  }

  async function submit(status: AnswerStatus, terminate: boolean) {
    if (!projectId || !currentQuestion) return;
    setError(null);

    let answerText: string | null = null;
    if (status === "answered") {
      if (selectedIdx !== null) {
        answerText = currentQuestion.options[selectedIdx];
      } else if (freeText.trim()) {
        answerText = freeText.trim();
      } else {
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
      if (!r.current_question || terminate) nav("/approve");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e.message ?? "Submit failed.");
    } finally {
      wsRef.current?.close();
      wsRef.current = null;
      setBusy(false);
    }
  }

  return (
    <section className="grid gap-6 md:grid-cols-3">
      <div className="md:col-span-2 space-y-4">
        <header>
          <h2 className="text-xl font-semibold">Stage 2 — Discovery</h2>
          <p className="text-sm text-muted-foreground">{projectName}</p>
        </header>

        <article className="rounded-lg border border-border bg-card p-5">
          <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
            Question {qaHistory.length + 1} · {currentQuestion.question_id}
          </p>
          <h3 className="text-lg font-semibold leading-snug">{currentQuestion.question}</h3>
          {currentQuestion.rationale && (
            <p className="mt-2 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Why this matters: </span>
              {currentQuestion.rationale}
            </p>
          )}

          <div className="mt-4 space-y-2">
            {currentQuestion.options.map((opt, i) => (
              <label
                key={i}
                className={`flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm ${
                  selectedIdx === i
                    ? "border-primary bg-primary/10"
                    : "border-border hover:bg-accent"
                }`}
              >
                <input
                  type="radio"
                  name="opt"
                  className="mt-1"
                  checked={selectedIdx === i}
                  onChange={() => {
                    setSelectedIdx(i);
                    setFreeText("");
                  }}
                />
                <span>{opt}</span>
              </label>
            ))}
          </div>

          <div className="mt-4 space-y-2">
            <label className="text-xs font-medium text-muted-foreground">
              Or write your own answer
            </label>
            <textarea
              rows={3}
              value={freeText}
              onChange={(e) => {
                setFreeText(e.target.value);
                if (e.target.value) setSelectedIdx(null);
              }}
              placeholder="Free-text answer (overrides any selected option)"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          {error && (
            <div className="mt-3 rounded-md border border-destructive/50 bg-destructive/10 p-2 text-sm text-destructive">
              {error}
            </div>
          )}

          {busy && (
            <div className="mt-4 rounded-md border border-border bg-muted/40 p-3">
              <p className="mb-2 flex items-center gap-2 text-xs font-medium">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
                Processing answer (LLM calls in progress)…
              </p>
              {liveEvents.length > 0 ? (
                <ul className="max-h-40 space-y-0.5 overflow-y-auto font-mono text-xs text-muted-foreground">
                  {liveEvents.map((line, i) => (
                    <li key={i}>· {line}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-muted-foreground">Waiting for first event…</p>
              )}
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-2">
            <button
              disabled={busy}
              onClick={() => submit("answered", false)}
              className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              Submit
            </button>
            <button
              disabled={busy}
              onClick={() => submit("deferred", false)}
              className="inline-flex h-9 items-center rounded-md border border-border px-4 text-sm font-medium hover:bg-accent disabled:opacity-50"
            >
              Defer
            </button>
            <button
              disabled={busy}
              onClick={() => submit("na", false)}
              className="inline-flex h-9 items-center rounded-md border border-border px-4 text-sm font-medium hover:bg-accent disabled:opacity-50"
            >
              Not Applicable
            </button>
            <button
              disabled={busy}
              onClick={() => submit("answered", true)}
              className="ml-auto inline-flex h-9 items-center rounded-md border border-destructive/40 px-4 text-sm font-medium text-destructive hover:bg-destructive/10 disabled:opacity-50"
            >
              I'm done — finish discovery
            </button>
          </div>
        </article>
      </div>

      <aside className="md:col-span-1">
        <h3 className="mb-2 text-sm font-medium text-muted-foreground">
          Q&A history ({qaHistory.length})
        </h3>
        {qaHistory.length === 0 && (
          <p className="text-xs text-muted-foreground">No previous questions yet.</p>
        )}
        <ul className="space-y-3">
          {qaHistory.map((qa) => (
            <li key={qa.question_id} className="rounded-md border border-border bg-card p-3 text-xs">
              <p className="font-medium leading-snug">{qa.question}</p>
              <p className="mt-1 text-muted-foreground">
                {qa.status === "answered" && (qa.answer || "(empty)")}
                {qa.status === "deferred" && "[Deferred]"}
                {qa.status === "na" && "[Not Applicable]"}
                {qa.status === "unknown" && "[Unknown]"}
              </p>
            </li>
          ))}
        </ul>
      </aside>
    </section>
  );
}
