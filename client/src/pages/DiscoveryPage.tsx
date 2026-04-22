/**
 * DiscoveryPage — Stage 2.
 * Interactive Q&A loop with the Discovery agent.
 *
 * TODO:
 *  - Poll or subscribe via WS for the next question (type: 'question').
 *  - Render prior Q&A history (answered / deferred / N-A).
 *  - After each answer, display the delta update from the analyser (highlighted).
 */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";

export default function DiscoveryPage() {
  const project = useAppStore((s) => s.project);
  const [current, setCurrent] = useState<string>("");
  const [answer, setAnswer] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    if (!project) return;
    projectsApi.getDiscovery(project.id).then((d: any) => setCurrent(d.current_question ?? ""));
  }, [project]);

  if (!project) return <p>No active project.</p>;

  async function submit(status: "answered" | "deferred" | "na") {
    if (!project) return;
    await projectsApi.answerDiscovery(project.id, answer, status);
    setAnswer("");
    const d: any = await projectsApi.getDiscovery(project.id);
    setCurrent(d.current_question ?? "");
  }

  return (
    <section className="card">
      <h2>Stage 2 — Discovery Q&amp;A</h2>
      {current ? (
        <>
          <p><strong>Agent asks:</strong> {current}</p>
          <textarea
            rows={4}
            style={{ width: "100%" }}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
          <div style={{ marginTop: ".5rem", display: "flex", gap: ".5rem" }}>
            <button onClick={() => submit("answered")}>Submit</button>
            <button onClick={() => submit("deferred")}>Defer (Ask Client)</button>
            <button onClick={() => submit("na")}>N/A</button>
          </div>
        </>
      ) : (
        <>
          <p>No more questions.</p>
          <button
            onClick={async () => {
              await projectsApi.approveStage(project.id, "discovery");
              nav("/architecture");
            }}
          >
            Approve & Continue →
          </button>
        </>
      )}
    </section>
  );
}
