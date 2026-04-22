/**
 * UploadPage — Stage 0.
 * Responsibilities:
 *  - create a new project
 *  - accept PDF/DOC/DOCX/PPT/PPTX/XLS/XLSX files (max 50 MB each)
 *  - capture free-text additional context
 *  - trigger Stage 1 analyser
 *
 * Styled with Tailwind utility classes + shadcn design tokens (see styles.css).
 * Once you install shadcn primitives, swap the raw <input> / <button> for:
 *     npx shadcn@latest add button input textarea card label
 * and replace the markup with <Button>, <Input>, etc.
 *
 * TODO:
 *  - Add drag-and-drop (react-dropzone) — see BRD §4.1 Should-Have.
 *  - Add extracted-text preview panel.
 *  - Add per-file validation feedback.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";

const ACCEPTED = ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx";
const MAX_SIZE = 50 * 1024 * 1024;

export default function UploadPage() {
  const [name, setName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [context, setContext] = useState("");
  const [busy, setBusy] = useState(false);
  const setProject = useAppStore((s) => s.setProject);
  const nav = useNavigate();

  async function handleStart() {
    if (!name || files.length === 0)
      return alert("Project name + at least 1 file required");
    setBusy(true);
    try {
      const project = await projectsApi.create(name);
      setProject(project);
      await projectsApi.uploadDocuments(project.id, files, context);
      await projectsApi.triggerAnalyse(project.id);
      nav("/analyser");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-3xl rounded-lg border border-border bg-card p-6 shadow-sm">
      <h2 className="mb-1 text-xl font-semibold">
        Stage 0 — Upload Requirement Documents
      </h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Drop your SOW, BRD or proposal to bootstrap the analysis pipeline.
      </p>

      <div className="space-y-5">
        <div className="space-y-2">
          <label htmlFor="project-name" className="text-sm font-medium">
            Project name
          </label>
          <input
            id="project-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Acme — Q2 engagement"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">
            Documents <span className="text-muted-foreground">(≤ 50 MB each)</span>
          </label>
          <input
            type="file"
            accept={ACCEPTED}
            multiple
            onChange={(e) => {
              const picked = Array.from(e.target.files ?? []).filter(
                (f) => f.size <= MAX_SIZE,
              );
              setFiles(picked);
            }}
            className="block w-full text-sm text-muted-foreground file:mr-4 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:opacity-90"
          />
          {files.length > 0 && (
            <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
              {files.map((f) => (
                <li key={f.name} className="flex justify-between">
                  <span>{f.name}</span>
                  <span>{(f.size / 1024 / 1024).toFixed(1)} MB</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="space-y-2">
          <label htmlFor="context" className="text-sm font-medium">
            Additional context <span className="text-muted-foreground">(optional)</span>
          </label>
          <textarea
            id="context"
            rows={5}
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Paste any extra client notes, URLs, or instructions for the Analyser agent."
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </div>

        <button
          disabled={busy}
          onClick={handleStart}
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground ring-offset-background transition-colors hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
        >
          {busy ? "Starting…" : "Start Analysis"}
        </button>
      </div>
    </section>
  );
}
