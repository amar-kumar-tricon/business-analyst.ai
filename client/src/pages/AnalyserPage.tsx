/**
 * AnalyserPage — Stage 1 readout.
 *
 * Read-only view of the Stage-1 analyser output that lives in the store.
 * No backend calls here; everything was populated by /run on the upload page.
 */
import { Link } from "react-router-dom";
import { useAppStore } from "../store/useAppStore";
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
    total >= 7
      ? "text-emerald-500"
      : total >= 5
      ? "text-amber-500"
      : "text-destructive";
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <h3 className="mb-3 text-sm font-medium text-muted-foreground">
        Completeness Score
      </h3>
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
  const { projectId, projectName, score, currentQuestion, finalDocReady } = useAppStore();

  if (!projectId) {
    return (
      <div className="rounded-md border border-border bg-card p-6 text-sm">
        No active project — start from the <Link to="/" className="text-primary underline">upload page</Link>.
      </div>
    );
  }

  if (!score) {
    return <p className="text-sm text-muted-foreground">Run not completed yet.</p>;
  }

  return (
    <section className="space-y-6">
      <header className="flex items-baseline justify-between">
        <div>
          <h2 className="text-xl font-semibold">Stage 1 — Analyser</h2>
          <p className="text-sm text-muted-foreground">{projectName}</p>
        </div>
        <div className="flex gap-2">
          {currentQuestion ? (
            <Link
              to="/discovery"
              className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              Continue to Discovery →
            </Link>
          ) : finalDocReady ? (
            <Link
              to="/approve"
              className="inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              Review & Approve →
            </Link>
          ) : null}
        </div>
      </header>

      <ScoreCard score={score} />

      <details className="rounded-lg border border-border bg-card p-5">
        <summary className="cursor-pointer text-sm font-medium">
          Per-criterion reasoning
        </summary>
        <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
          {Object.entries(score.per_criterion_reasoning ?? {}).map(([k, v]) => (
            <li key={k}>
              <span className="font-medium text-foreground">{CRITERION_LABELS[k] ?? k}: </span>
              {v}
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
