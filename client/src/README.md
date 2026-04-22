# `client/src/` — File-by-file guide

## `App.tsx` / `main.tsx`
- `main.tsx` — Vite entry point. Mounts `<App />` into `#root` and imports `styles.css` (Tailwind directives + shadcn CSS variables).
- `App.tsx` — top-level router. Renders the stage-stepper and switches page by `useAppStore().activeStage`.

## `api/`
Thin `fetch` + `WebSocket` wrappers. One file per backend resource.

| File | Purpose |
|------|---------|
| `http.ts` | Base `fetch` helper — handles JSON, error normalisation, base URL (`/api`). Import from here, never call `fetch()` directly in pages. |
| `projects.ts` | `createProject`, `getProject`, `approve(stage)`, `analyse`, `regenerateArchitecture`, `finalize`, `exportStage`. |
| `settings.ts` | `getLLMConfig`, `updateLLMConfig(agentId, cfg)`. |
| `ws.ts` | `connectProjectStream(projectId, onEvent)` — handles reconnect + JSON parsing of `token / question / stage_complete / error` events. |

## `pages/`
One page per pipeline stage. Pages own the UI; they call `api/*` and `store/*`
but contain no business logic.

| File | Stage | Responsibility |
|------|:-----:|----------------|
| `UploadPage.tsx` | 0 | Project create + drag-drop multi-upload + paste additional context. |
| `AnalyserPage.tsx` | 1 | Renders Stage 1 result, allows inline edits, hits `/approve/analyser`. |
| `DiscoveryPage.tsx` | 2 | Q&A chat UI; calls `/discovery/answer` with `answer / defer / na`. |
| `ArchitecturePage.tsx` | 3 | Renders Mermaid diagrams client-side via the `mermaid` npm package; shows PlantUML DSL in a code block (or via public PlantUML service). |
| `SprintPage.tsx` | 4 | Burndown + sprint/story table + team composition. |
| `SettingsPage.tsx` | — | Per-agent LLM provider/model configuration. |

## `store/`
Zustand store: `activeProjectId`, `activeStage`, `stageOutputs`, `wsEvents[]`.
Pages subscribe with selectors so re-renders stay cheap.

## `types/`
TypeScript mirrors of backend Pydantic schemas (`app/schemas/`). Keep in sync
manually when schemas change.

## `lib/`
- `utils.ts` — the `cn()` helper (`clsx` + `tailwind-merge`) required by shadcn components.

## `components/`
Hand-written reusable components + **`components/ui/`** which is owned by the
shadcn CLI. Run `npx shadcn@latest add <name>` to drop a new primitive in.
