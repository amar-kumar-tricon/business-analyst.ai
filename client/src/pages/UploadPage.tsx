/**
 * UploadPage — Stage 0.
 *
 * Flow on submit:
 *   1. POST /projects                       — create the project shell
 *   2. POST /projects/{id}/files (per file) — upload + parse each document
 *   3. Fire POST /projects/{id}/run         — DON'T await; navigate to /analyser
 *      so the user sees live progress while the long LLM pipeline runs.
 *      The promise resolves into the store (applyRun / setRunError).
 *
 * Backend supports .md / .markdown / .txt / .csv / .json / .pdf / .docx.
 */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { useAppStore } from "../store/useAppStore";

const ACCEPTED = ".md,.markdown,.txt,.csv,.json,.pdf,.docx";
const MAX_SIZE = 50 * 1024 * 1024;

export default function UploadPage() {
  const [name, setName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [context, setContext] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusLine, setStatusLine] = useState<string>("");

  const setProject = useAppStore((s) => s.setProject);
  const applyRun = useAppStore((s) => s.applyRun);
  const setRunning = useAppStore((s) => s.setRunning);
  const setRunError = useAppStore((s) => s.setRunError);
  const reset = useAppStore((s) => s.reset);
  const nav = useNavigate();

  async function handleStart() {
    setError(null);
    if (!name.trim()) return setError("Project name is required.");
    if (files.length === 0) return setError("Upload at least one document.");

    setBusy(true);
    reset();
    try {
      setStatusLine("Creating project…");
      const created = await projectsApi.create(name.trim(), context);
      setProject(created.project_id, name.trim());

      for (const file of files) {
        setStatusLine(`Uploading & parsing ${file.name}…`);
        await projectsApi.uploadFile(created.project_id, file);
      }

      // Kick off the long-running Stage 1 + 2 pipeline. Don't await — the
      // analyser page will show live progress and pick up the result via the
      // store as soon as the promise resolves.
      setRunning(true);
      projectsApi
        .run(created.project_id)
        .then((r) => applyRun(r))
        .catch((e: any) => {
          setRunError(e?.response?.data?.detail ?? e?.message ?? "Run failed.");
          setRunning(false);
        });

      nav("/analyser");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e.message ?? "Something went wrong.");
    } finally {
      setBusy(false);
      setStatusLine("");
    }
  }

  return (
    <section className="mx-auto max-w-3xl rounded-lg border border-border bg-card p-6 shadow-sm">
      <h2 className="mb-1 text-xl font-semibold">Stage 0 — Upload Requirement Documents</h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Drop your BRD or proposal to bootstrap the analysis pipeline. Supported:{" "}
        <code>.pdf</code>, <code>.docx</code>, <code>.md</code>, <code>.txt</code>,{" "}
        <code>.csv</code>, <code>.json</code>.
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
            placeholder="Acme — Helpdesk Portal"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
              const picked = Array.from(e.target.files ?? []).filter((f) => f.size <= MAX_SIZE);
              setFiles(picked);
            }}
            className="block w-full text-sm text-muted-foreground file:mr-4 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:opacity-90"
          />
          {files.length > 0 && (
            <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
              {files.map((f) => (
                <li key={f.name} className="flex justify-between">
                  <span>{f.name}</span>
                  <span>{(f.size / 1024 / 1024).toFixed(2)} MB</span>
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
            placeholder="Any extra notes, URLs, or instructions for the Analyser agent."
            className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        {error && (
          <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {busy && statusLine && (
          <div className="rounded-md border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
            {statusLine}
          </div>
        )}

        <button
          disabled={busy}
          onClick={handleStart}
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:opacity-90 disabled:pointer-events-none disabled:opacity-50"
        >
          {busy ? "Working…" : "Start Analysis"}
        </button>
      </div>
    </section>
  );
}
