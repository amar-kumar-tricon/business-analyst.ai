/**
 * ArchitecturePage — Stage 3.
 * Renders Mermaid diagrams in-browser and PlantUML SVGs returned from the server.
 *
 * TODO:
 *  - Add editable Mermaid DSL textarea with live-preview (re-render on change).
 *  - Add "Regenerate" button calling /architecture/regenerate.
 *  - Add SVG / PNG download links per diagram.
 */
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import mermaid from "mermaid";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";
import type { ArchitectureResult } from "../types";

mermaid.initialize({ startOnLoad: false, theme: "dark" });

export default function ArchitecturePage() {
  const project = useAppStore((s) => s.project);
  const [data, setData] = useState<ArchitectureResult | null>(null);
  const mermaidRef = useRef<HTMLDivElement>(null);
  const nav = useNavigate();

  useEffect(() => {
    if (!project) return;
    projectsApi.getArchitecture(project.id).then((d: ArchitectureResult) => setData(d));
  }, [project]);

  useEffect(() => {
    if (data && mermaidRef.current) mermaid.run({ nodes: [mermaidRef.current] });
  }, [data]);

  if (!project) return <p>No active project.</p>;
  if (!data) return <p>Generating architecture diagrams…</p>;

  return (
    <section className="card">
      <h2>Stage 3 — Architecture Diagrams</h2>

      {data.mermaid.map((d) => (
        <div key={d.id} className="card">
          <h3>{d.title} (Mermaid)</h3>
          <div ref={mermaidRef} className="mermaid">{d.dsl}</div>
        </div>
      ))}

      {data.plantuml.map((d) => (
        <div key={d.id} className="card">
          <h3>{d.title} (PlantUML)</h3>
          {d.svg && <div dangerouslySetInnerHTML={{ __html: d.svg }} />}
        </div>
      ))}

      <button
        onClick={async () => {
          await projectsApi.approveStage(project.id, "architecture");
          nav("/sprint");
        }}
      >
        Approve & Continue →
      </button>
    </section>
  );
}
