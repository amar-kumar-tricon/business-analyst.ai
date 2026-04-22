/**
 * SprintPage — Stage 4.
 * Displays the Sprint Planner output (totals + sprint-by-sprint board) and
 * finalises the project to create a version snapshot.
 *
 * TODO:
 *  - Render sprints as columns (Kanban-style).
 *  - Show MVP cut-off badge at the right sprint.
 *  - Add export-to-DOCX button.
 */
import { useEffect, useState } from "react";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";
import type { SprintPlan } from "../types";

export default function SprintPage() {
  const project = useAppStore((s) => s.project);
  const [plan, setPlan] = useState<SprintPlan | null>(null);
  const [finalized, setFinalized] = useState(false);

  useEffect(() => {
    if (!project) return;
    projectsApi.getSprint(project.id).then((d: SprintPlan) => setPlan(d));
  }, [project]);

  if (!project) return <p>No active project.</p>;
  if (!plan) return <p>Generating sprint plan…</p>;

  return (
    <section className="card">
      <h2>Stage 4 — Sprint Plan</h2>
      <p>
        {plan.total_sprints} sprints · {plan.total_story_points} points · {plan.total_man_hours} hrs · MVP @ sprint {plan.mvp_cutoff_sprint}
      </p>

      {plan.sprints.map((s) => (
        <div key={s.number} className="card">
          <h3>Sprint {s.number}: {s.goal}</h3>
          <ul>
            {s.stories.map((st) => (
              <li key={st.id}>
                <strong>[{st.points}pt · {st.role}]</strong> {st.title}
              </li>
            ))}
          </ul>
        </div>
      ))}

      {!finalized ? (
        <button
          onClick={async () => {
            await projectsApi.finalize(project.id);
            setFinalized(true);
          }}
        >
          Finalize & Snapshot v{project.version + 1}
        </button>
      ) : (
        <p>✅ Project finalized — snapshot created.</p>
      )}
    </section>
  );
}
