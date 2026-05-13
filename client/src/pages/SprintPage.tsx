/**
 * SprintPage — Stage 4 Sprint Planner.
 *
 * Calls POST /api/projects/{project_id}/sprint and renders the returned
 * SprintPlan as a set of tables: summary, sprints (with stories), team
 * composition, tech stack, and risk register.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";
import type { SprintPlan } from "../types";

export default function SprintPage() {
  const projectId = useAppStore((s) => s.projectId);
  const nav = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<SprintPlan | null>(null);
  const [approved, setApproved] = useState(false);

  async function handleGenerate() {
    if (!projectId) {
      setError("No active project. Please upload a document first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await projectsApi.generateSprint(projectId);
      if (!res.sprint_plan) {
        setError("Backend returned an empty sprint plan.");
      } else {
        setPlan(res.sprint_plan);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setError(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <section className="rounded-lg border border-border bg-card p-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Stage 4 — Sprint Planner</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Generate a sprint breakdown with story points, team composition, and
            risk register.
          </p>
        </div>
        {!plan && (
          <button
            onClick={handleGenerate}
            disabled={busy}
            className="rounded-md bg-primary px-5 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50 hover:bg-primary/90 transition-colors"
          >
            {busy ? "Generating…" : "Generate Sprint"}
          </button>
        )}
        {plan && !approved && (
          <div className="flex gap-2">
            <button
              onClick={() => nav("/analyser")}
              className="rounded-md border border-destructive px-5 py-2 text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors"
            >
              Deny
            </button>
            <button
              onClick={() => setApproved(true)}
              className="rounded-md bg-primary px-5 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Approve
            </button>
          </div>
        )}
        {plan && approved && (
          <span className="rounded-full bg-green-500/20 px-4 py-1.5 text-sm font-medium text-green-400">
            ✓ Approved
          </span>
        )}
      </section>

      {error && (
        <div className="rounded-md border border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {plan && (
        <>
          {/* Summary bar */}
          <section className="rounded-lg border border-border bg-card p-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { label: "Total Sprints", value: plan.total_sprints },
              { label: "Sprint Duration", value: `${plan.sprint_duration_weeks}w` },
              { label: "Total Story Points", value: plan.total_story_points },
              { label: "Total Man-Hours", value: plan.total_man_hours },
            ].map(({ label, value }) => (
              <div key={label} className="text-center">
                <p className="text-2xl font-bold">{value}</p>
                <p className="text-xs text-muted-foreground">{label}</p>
              </div>
            ))}
          </section>

          {/* Sprints */}
          {plan.sprints.map((sprint) => (
            <section
              key={sprint.sprint_number}
              className="rounded-lg border border-border bg-card overflow-hidden"
            >
              <div className="flex items-center gap-3 px-5 py-3 border-b border-border bg-muted/30">
                <span className="font-semibold">
                  Sprint {sprint.sprint_number} — {sprint.sprint_name}
                </span>
                {sprint.is_mvp_cutoff && (
                  <span className="rounded-full bg-primary/20 px-2 py-0.5 text-xs font-medium text-primary">
                    MVP cutoff
                  </span>
                )}
                <span className="ml-auto text-sm text-muted-foreground">
                  {sprint.total_points} pts · {sprint.man_hours} hrs
                </span>
              </div>
              <p className="px-5 py-2 text-sm text-muted-foreground italic">
                {sprint.goal}
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/20 text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="px-4 py-2 text-left">ID</th>
                      <th className="px-4 py-2 text-left">Title</th>
                      <th className="px-4 py-2 text-left">Description</th>
                      <th className="px-4 py-2 text-center">Points</th>
                      <th className="px-4 py-2 text-left">Role</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sprint.stories.map((story) => (
                      <tr
                        key={story.story_id}
                        className="border-b border-border last:border-0 hover:bg-muted/10"
                      >
                        <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                          {story.story_id}
                        </td>
                        <td className="px-4 py-2 font-medium">{story.title}</td>
                        <td className="px-4 py-2 text-muted-foreground">
                          {story.description}
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span className="rounded-full bg-muted px-2 py-0.5 text-xs">
                            {story.story_points}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-muted-foreground">
                          {story.role}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}

          {/* Team Composition */}
          <section className="rounded-lg border border-border bg-card overflow-hidden">
            <h3 className="px-5 py-3 font-semibold border-b border-border">
              Team Composition
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="px-4 py-2 text-left">Role</th>
                    <th className="px-4 py-2 text-center">Count</th>
                    <th className="px-4 py-2 text-center">Hrs / Sprint</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.team_composition.map((m) => (
                    <tr
                      key={m.role}
                      className="border-b border-border last:border-0 hover:bg-muted/10"
                    >
                      <td className="px-4 py-2">{m.role}</td>
                      <td className="px-4 py-2 text-center">{m.count}</td>
                      <td className="px-4 py-2 text-center">{m.hours_per_sprint}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Tech Stack */}
          <section className="rounded-lg border border-border bg-card overflow-hidden">
            <h3 className="px-5 py-3 font-semibold border-b border-border">
              Technology Stack
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/20 text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="px-4 py-2 text-left">Component</th>
                    <th className="px-4 py-2 text-left">Technology</th>
                    <th className="px-4 py-2 text-left">Rationale</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.technology_stack.map((t) => (
                    <tr
                      key={t.component}
                      className="border-b border-border last:border-0 hover:bg-muted/10"
                    >
                      <td className="px-4 py-2 font-medium">{t.component}</td>
                      <td className="px-4 py-2">{t.technology}</td>
                      <td className="px-4 py-2 text-muted-foreground">{t.rationale}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Risk Register */}
          {plan.risk_register.length > 0 && (
            <section className="rounded-lg border border-border bg-card overflow-hidden">
              <h3 className="px-5 py-3 font-semibold border-b border-border">
                Risk Register
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/20 text-xs uppercase tracking-wide text-muted-foreground">
                      <th className="px-4 py-2 text-left">ID</th>
                      <th className="px-4 py-2 text-left">Description</th>
                      <th className="px-4 py-2 text-left">Category</th>
                      <th className="px-4 py-2 text-left">Severity</th>
                      <th className="px-4 py-2 text-left">Mitigation</th>
                      <th className="px-4 py-2 text-center">Sprint</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plan.risk_register.map((r) => (
                      <tr
                        key={r.risk_id}
                        className="border-b border-border last:border-0 hover:bg-muted/10"
                      >
                        <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                          {r.risk_id}
                        </td>
                        <td className="px-4 py-2">{r.description}</td>
                        <td className="px-4 py-2 capitalize">{r.category}</td>
                        <td className="px-4 py-2">
                          <span
                            className={
                              r.severity === "high"
                                ? "text-destructive font-medium"
                                : r.severity === "medium"
                                ? "text-yellow-500"
                                : "text-muted-foreground"
                            }
                          >
                            {r.severity}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-muted-foreground">
                          {r.mitigation}
                        </td>
                        <td className="px-4 py-2 text-center">
                          {r.sprint_impacted ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          <p className="text-right text-xs text-muted-foreground">
            Generated at {new Date(plan.generated_at).toLocaleString()}
          </p>
        </>
      )}
    </div>
  );
}
