/**
 * UploadPage — Stage 0.
 *
 * Flow on submit:
 *   1. POST /projects                    — create the project shell
 *   2. POST /projects/{id}/files (per file) — upload + parse each document
 *   3. POST /projects/{id}/run           — run Stage 1 + Stage 2 (until first question)
 *   4. Navigate to /discovery (if a question came back) or /approve (otherwise)
 *
 * Backend parser currently understands .md / .markdown / .txt / .csv / .json.
 * Other file types are accepted by the input but will be best-effort plain-text.
 */
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { projectsApi } from "../api/projects";
import { openProjectStream } from "../api/ws";
import { formatEventSummary } from "../lib/events";
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
  const [liveEvents, setLiveEvents] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const setProject = useAppStore((s) => s.setProject);
  const applyRun = useAppStore((s) => s.applyRun);
  const reset = useAppStore((s) => s.reset);
  const nav = useNavigate();

  useEffect(() => {
    return () => {
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, []);

  async function handleStart() {
    setError(null);
    if (!name.trim()) return setError("Project name is required.");
    if (files.length === 0) return setError("Upload at least one document.");

    setBusy(true);
    setLiveEvents([]);
    reset();
    try {
      setStatusLine("Creating project…");
      const created = await projectsApi.create(name.trim(), context);
      setProject(created.project_id, name.trim());

      // Open WS so the user sees node-by-node progress while /run is in flight.
      wsRef.current?.close();
      wsRef.current = openProjectStream(created.project_id, (e) => {
        setLiveEvents((prev) => [...prev, formatEventSummary(e)]);
      });

      for (const file of files) {
        setStatusLine(`Uploading & parsing ${file.name}…`);
        await projectsApi.uploadFile(created.project_id, file);
      }

      setStatusLine("Running Stage 1 + Stage 2 — this can take a couple of minutes for large BRDs.");
      const run = await projectsApi.run(created.project_id);
      applyRun(run);

      nav(run.current_question ? "/discovery" : "/approve");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? e.message ?? "Something went wrong.");
    } finally {
      wsRef.current?.close();
      wsRef.current = null;
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

        {busy && (
          <div className="rounded-md border border-border bg-muted/40 p-3">
            {statusLine && (
              <p className="mb-2 flex items-center gap-2 text-sm font-medium text-foreground">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
                {statusLine}
              </p>
            )}
            {liveEvents.length > 0 ? (
              <ul className="max-h-48 space-y-0.5 overflow-y-auto font-mono text-xs text-muted-foreground">
                {liveEvents.map((line, i) => (
                  <li key={i}>· {line}</li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-muted-foreground">Waiting for first event…</p>
            )}
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
