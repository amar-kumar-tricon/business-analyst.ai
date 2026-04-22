/**
 * AnalyserPage — Stage 1.
 * Shows the structured Analyser output and offers an "Approve & Continue" button.
 *
 * TODO:
 *  - Render each section (exec summary, MoSCoW reqs, risks, team, score) as editable cards.
 *  - Wire inline-edit save back to POST /projects/:id/approve/analyse with `edits` payload.
 *  - Add export-to-PDF / DOCX button.
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";
import type { AnalyserResult } from "../types";

export default function AnalyserPage() {
  const project = useAppStore((s) => s.project);
  const [data, setData] = useState<AnalyserResult | null>(null);
  const nav = useNavigate();

  useEffect(() => {
    if (!project) return;
    projectsApi.get(project.id).then((p: any) => setData(p.analyser_output ?? null));
  }, [project]);

  if (!project) return <p>No active project. Go to Upload first.</p>;
  if (!data) return <p>Running Analyser agent…</p>;

  return (
    <section className="card">
      <h2>Stage 1 — Analyser Output</h2>
      <h3>Executive Summary</h3>
      <p>{data.executive_summary}</p>

      <h3>Completeness Score: {data.completeness_score.total} / 10</h3>

      <h3>Open Questions</h3>
      <ul>{data.open_questions.map((q, i) => <li key={i}>{q}</li>)}</ul>

      <button
        onClick={async () => {
          await projectsApi.approveStage(project.id, "analyse");
          nav("/discovery");
        }}
      >
        Approve & Continue →
      </button>
    </section>
  );
}
