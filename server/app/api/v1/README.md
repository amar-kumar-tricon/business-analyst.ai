# `app/api/v1/` — REST + WebSocket routers

**Yes, every resource here is a FastAPI router.** Each file declares a
`router = APIRouter(prefix=..., tags=[...])` and `router.py` aggregates them
into the single `api_router` that `main.py` mounts under `/api`.

## How routers are wired

```
main.py
  └─ app.include_router(api_router, prefix="/api")   # REST
  └─ app.include_router(ws_router)                    # WebSocket (prefix="/ws")

api/v1/router.py
  └─ api_router.include_router(projects.router)
  └─ api_router.include_router(documents.router)
  └─ ...(one per resource file)
```

Adding a new resource:
1. create `app/api/v1/<name>.py` with `router = APIRouter(prefix="/<name>", tags=["<name>"])`
2. import it in `router.py` and call `api_router.include_router(<name>.router)`

## Files

| File | Endpoints it owns | Purpose |
|------|-------------------|---------|
| `router.py` | — | Aggregates every resource router into `api_router`. |
| `projects.py` | `POST /projects`, `GET /projects/{id}`, `POST /projects/{id}/approve/{stage}` | Project lifecycle + human approval gates (advances LangGraph past an `interrupt_before`). |
| `documents.py` | `POST /projects/{id}/documents` | Multi-file upload. Validates ext + size, saves to `uploads/<project_id>/` via `services.local_storage`. |
| `analyse.py` | `POST /projects/{id}/analyse` | Kicks off Stage 1 (Analyser agent) as a background task. |
| `discovery.py` | `GET /projects/{id}/discovery`, `POST /projects/{id}/discovery/answer` | Stage 2 Q&A loop — returns next question, accepts answer/defer/N-A. |
| `architecture.py` | `GET /projects/{id}/architecture`, `POST /projects/{id}/architecture/regenerate` | Stage 3 diagrams (Mermaid + PlantUML DSL). |
| `sprint.py` | `GET /projects/{id}/sprint` | Stage 4 sprint plan. |
| `versions.py` | `POST /projects/{id}/finalize`, `GET /projects/{id}/versions` | Immutable snapshot creation + listing. |
| `export.py` | `POST /projects/{id}/export` | Exports any stage as PDF or DOCX via `services.export_service`. |
| `settings.py` | `GET /settings/llm-config`, `PUT /settings/llm-config/{agent_id}` | Per-agent LLM provider + model configuration. |
| `websocket.py` | `WS /ws/projects/{id}/stream` | Token-level streaming from agents to UI (events: `token` / `question` / `stage_complete` / `error`). |

## Rules for route handlers

- Keep them **thin**. Parse request → call a `service` or `agents.graph` function → return response.
- Never write SQL or LangChain code here.
- Validate inputs via Pydantic schemas in `app/schemas/`.
- Wire DB access via `Depends(get_db)` from `app/db/session.py`.
