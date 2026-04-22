# BRA Tool — Server

FastAPI + LangGraph backend. **Runs entirely locally** — SQLite file + local
`uploads/` and `exports/` folders. No Docker, no S3, no Java.

## 📂 Package Layout

```
app/
├── main.py                       ← FastAPI app factory + startup lifecycle
├── core/                         ← Cross-cutting primitives (config + logging)
├── api/v1/                       ← REST + WebSocket routers (1 file per resource)
├── agents/                       ← LangGraph agent layer
│   ├── state.py                  · GraphState TypedDict (the shared memory)
│   ├── graph.py                  · StateGraph wiring with interrupt_before gates
│   ├── llm_factory.py            · Build LLM client from llm_configs row
│   ├── analyser/                 · STAGE 1
│   ├── discovery/                · STAGE 2
│   ├── architecture/             · STAGE 3
│   └── sprint/                   · STAGE 4
├── services/                     ← Business logic (parsing, storage, diagrams, exports)
├── db/                           ← SQLAlchemy session + ORM models
└── schemas/                      ← Pydantic request/response schemas
```

Every folder above has its own `README.md` explaining what each `.py` file does.

## 🏁 Run

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # paste your OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

- API docs:  <http://localhost:8000/docs>
- SQLite DB: `bra_tool.db` (auto-created on first request)
- Uploads:   `uploads/<project_id>/`
- Exports:   `exports/<project_id>/`

## 🧑‍💻 "Where Do I Start?" — Checklist

1. **Implement an endpoint** — open the matching file in [app/api/v1/](app/api/v1/).
   Each file has a `router = APIRouter(...)` and TODO-marked stubs.
2. **Change how an agent thinks** — edit its `prompts.py` or add a tool in `tools.py`.
3. **Change the pipeline wiring** — [app/agents/graph.py](app/agents/graph.py). The graph edges and `interrupt_before=[...]` checkpoints are all declared in one place.
4. **Add a database field** — edit the model in [app/db/models/](app/db/models/) and add an Alembic migration later.
5. **Add a new file parser** — add a branch in [app/services/document_parser.py](app/services/document_parser.py).

> **Rule of thumb:** *Routes stay thin — business logic lives in `services/` or `agents/`.*

## 📈 Observability

- Set `LANGSMITH_API_KEY` in `.env` to enable LangSmith tracing automatically.
- Structured logs are configured in [app/core/logging.py](app/core/logging.py).
