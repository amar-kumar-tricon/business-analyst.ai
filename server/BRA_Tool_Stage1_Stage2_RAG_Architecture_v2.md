# BRA Tool — Stage 1 + Stage 2 + RAG Architecture

**Scope:** Document Analyser Agent (Stage 1) + Discovery / QnA Agent (Stage 2) + RAG indexing layer
**Owner:** Single engineer (parent graph + both subgraphs)
**Environment:** **Local development only** — everything runs on a single laptop via Docker Compose. No cloud infrastructure.
**Stack:** LangGraph · FastAPI · PostgreSQL + pgvector (Docker) · Redis (Docker) · MinIO (Docker, S3-compatible) · Local filesystem
**Auth:** **No authentication in this phase.** All endpoints are open. Auth (JWT/OAuth) is deferred to a later phase. Code should NOT be retrofitted with auth assumptions — keep handlers clean of user-context concerns for now.
**Out of scope (this doc):** Stage 3 (Architecture Agent), Stage 4 (Sprint Planning Agent), Frontend implementation, Authentication, Production deployment

---

## Table of Contents

1. [Design Decisions](#1-design-decisions)
2. [Local Infrastructure (Docker Compose)](#2-local-infrastructure-docker-compose)
3. [Architectural Overview](#3-architectural-overview)
4. [Complete Graph Topology](#4-complete-graph-topology)
5. [State Schemas](#5-state-schemas)
6. [Code Structure](#6-code-structure)
7. [Analyser Subgraph](#7-analyser-subgraph)
8. [Discovery Subgraph](#8-discovery-subgraph)
9. [Parent Graph](#9-parent-graph)
10. [Node-by-Node Specification](#10-node-by-node-specification)
11. [RAG Strategy — Dual Index](#11-rag-strategy--dual-index)
12. [Question Generation Strategy](#12-question-generation-strategy)
13. [Per-Agent LLM Configuration](#13-per-agent-llm-configuration)
14. [Streaming Layer](#14-streaming-layer)
15. [Resume Mechanics (Interrupts)](#15-resume-mechanics-interrupts)
16. [Database Schema](#16-database-schema)
17. [API Endpoints](#17-api-endpoints)
18. [Implementation Gotchas](#18-implementation-gotchas)
19. [Build Order](#19-build-order)
20. [Pre-Build Contracts to Lock](#20-pre-build-contracts-to-lock)

---

## 1. Design Decisions

Four foundational decisions drive the entire architecture:

| Decision | Choice | Rationale |
|---|---|---|
| **Graph structure** | Parent graph with Analyser & Discovery as nested compiled subgraphs | Each subgraph independently testable; clean boundaries; future Stage 3/4 plug in identically; per-agent LLM config is natural |
| **RAG timing** | Both pre-approval (working chunks, TTL) and post-approval (permanent requirement_nodes) | Pre-approval enables in-flight retrieval for the agent during reasoning; post-approval is the canonical, versioned, long-term index |
| **Environment** | Local-only via Docker Compose | No cloud infra available. Single laptop. PostgreSQL+pgvector, Redis, MinIO all run as containers. App runs natively on the host. |
| **Authentication** | None in this phase | Skip auth entirely. Endpoints are open. Adding it later means dropping a middleware in front of FastAPI — keep handlers free of `current_user` parameters and DB tables free of `user_id` foreign keys for now. |

**Subgraph composition rule (critical):** Analyser and Discovery are *not* monolithic agents. Each is a small internal state machine of nodes. They are merged at the *workflow* level (sharing state, sequenced behind a single approval gate) but split at the *implementation* level (different prompts, different tools, different output schemas).

**No-auth implementation rule:** Don't write `Depends(get_current_user)` anywhere. Don't add `created_by UUID` columns. Don't pass user IDs through the graph state. When auth is added later, it'll be a clean cross-cutting addition: a middleware, a `users` table, a few foreign keys, and a couple of `Depends()` injections. Polluting the codebase with auth scaffolding now creates technical debt for a feature you don't need yet.

---

## 2. Local Infrastructure (Docker Compose)

Everything except the FastAPI app itself runs in Docker. The app runs on the host machine for fast iteration, hot reload, and easy debugging.

### 2.1 Service inventory

| Service | Image | Port (host) | Purpose |
|---|---|---|---|
| **postgres** | `pgvector/pgvector:pg16` | `5432` | Application data + pgvector extension + LangGraph checkpointer |
| **redis** | `redis:7-alpine` | `6379` | Pub/sub for streaming events between graph runner and WS handlers |
| **minio** | `minio/minio:latest` | `9000` (API), `9001` (console) | S3-compatible object store for raw uploads and rendered exports |
| **adminer** *(optional)* | `adminer:latest` | `8080` | Web UI for inspecting Postgres during development |

The `pgvector/pgvector` image is the official build with the `vector` extension preinstalled — saves you from building it yourself.

### 2.2 docker-compose.yml

```yaml
# infra/docker-compose.yml

version: "3.9"

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: bra_postgres
    environment:
      POSTGRES_USER: bra
      POSTGRES_PASSWORD: bra_local_dev
      POSTGRES_DB: bra
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init/01_extensions.sql:/docker-entrypoint-initdb.d/01_extensions.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bra -d bra"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    container_name: bra_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--appendonly", "yes"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  minio:
    image: minio/minio:latest
    container_name: bra_minio
    environment:
      MINIO_ROOT_USER: bra_minio
      MINIO_ROOT_PASSWORD: bra_minio_local_dev
    ports:
      - "9000:9000"     # API
      - "9001:9001"     # Web console
    volumes:
      - minio_data:/data
    command: ["server", "/data", "--console-address", ":9001"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  adminer:
    image: adminer:latest
    container_name: bra_adminer
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### 2.3 Postgres init script

```sql
-- infra/init/01_extensions.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- helpful for fuzzy text matching
```

This runs once on first container creation. Subsequent restarts skip it.

### 2.4 MinIO bucket bootstrap

MinIO needs buckets created before the app uses them. Add a one-time setup script:

```bash
# infra/setup_minio.sh
#!/usr/bin/env bash
set -e

# Wait for MinIO to be ready
until curl -f http://localhost:9000/minio/health/live > /dev/null 2>&1; do
  echo "Waiting for MinIO..."
  sleep 2
done

# Use the mc (MinIO client) container to create buckets
docker run --rm --network host \
  -e MC_HOST_local="http://bra_minio:bra_minio_local_dev@localhost:9000" \
  minio/mc:latest \
  /bin/sh -c "
    mc mb local/bra-uploads --ignore-existing
    mc mb local/bra-exports --ignore-existing
    mc anonymous set download local/bra-exports
  "

echo "MinIO buckets ready."
```

Two buckets:
- `bra-uploads` — raw user-uploaded documents (private)
- `bra-exports` — rendered PDFs/DOCX of approved analysis (download-anonymous for local dev simplicity; tighten when adding auth)

### 2.5 Environment configuration

Use a single `.env` file at the repo root. The app reads it via `pydantic-settings`.

```env
# .env (repo root, NEVER commit)

# ── Database ──
DATABASE_URL=postgresql+psycopg://bra:bra_local_dev@localhost:5432/bra
DATABASE_URL_SYNC=postgresql://bra:bra_local_dev@localhost:5432/bra

# ── Redis ──
REDIS_URL=redis://localhost:6379/0

# ── MinIO (S3-compatible) ──
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=bra_minio
S3_SECRET_KEY=bra_minio_local_dev
S3_REGION=us-east-1
S3_BUCKET_UPLOADS=bra-uploads
S3_BUCKET_EXPORTS=bra-exports

# ── LLM Providers ──
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# ── App ──
APP_ENV=local
LOG_LEVEL=DEBUG
APP_HOST=127.0.0.1
APP_PORT=8000
```

Add `.env.example` (committed, with placeholder values) so a new dev can copy and fill it in.

### 2.6 Why MinIO instead of just using the local filesystem

You could use `/var/data/uploads` directly. Don't. Reasons:

1. **Production parity.** The S3 SDK code you write today (`boto3` + `endpoint_url`) works identically against AWS S3 later. Zero code change to migrate.
2. **Signed URLs.** Frontend can download exports directly from MinIO via pre-signed URLs without proxying through your API. Same pattern as production.
3. **Versioning, lifecycle, multipart upload.** All work locally if you want them.
4. **Cleaner deletion.** You'll periodically purge old uploads; bucket-scoped `delete_objects` is cleaner than `os.remove()` loops.

### 2.7 Bring-up commands

```bash
# One-time setup
cd infra
docker compose up -d
./setup_minio.sh
cd ..

# Run app (separate terminal)
cp .env.example .env  # fill in API keys
poetry install
poetry run uvicorn bra_agents.api.main:app --reload --host 127.0.0.1 --port 8000

# Verify
curl http://localhost:8000/health
```

### 2.8 Useful local URLs

| URL | Purpose |
|---|---|
| `http://localhost:8000/docs` | FastAPI Swagger UI |
| `http://localhost:8000/health` | Liveness check |
| `http://localhost:8001` | LangGraph Studio (if installed) — visualize graph runs |
| `http://localhost:9001` | MinIO web console (browse uploaded files) |
| `http://localhost:8080` | Adminer (browse Postgres tables) |
| `redis-cli -h localhost` | Inspect pub/sub channels |

### 2.9 Local-only simplifications you should accept

These are deliberately simpler than production. Don't over-engineer:

- **No HTTPS.** Plain HTTP on localhost. Don't waste time on self-signed certs.
- **No load balancer.** Single uvicorn process with `--reload`.
- **No worker pool.** FastAPI `BackgroundTasks` is enough for ingestion; ARQ is overkill at this stage.
- **No secrets manager.** `.env` file. When auth lands, switch to a real one.
- **No backup/replication.** Postgres data is in a Docker volume; that's it.
- **Single-tenant.** No need to scope queries by org/team. Just `project_id`.
- **MinIO bucket policies are loose.** `bra-exports` is publicly downloadable by anyone with the URL. Fine for local. Tighten later.

### 2.10 What changes when auth is added (for context)

So the design choices made now don't cause pain later, here's the future migration sketch — **do not implement any of this now**:

- Add `users` table + auth provider integration (OAuth/JWT).
- Add `created_by UUID REFERENCES users(id)` to `projects`, `documents`, `stage_outputs`.
- Add a FastAPI dependency `get_current_user()` and apply it via a router-level `dependencies=[...]`.
- Add `user_id` to WebSocket connection scope so events are gated.
- Switch MinIO bucket policies to private + signed URLs only.
- Add row-level security or app-level filtering by `user_id` on queries.

The point: every one of these is an *additive* change to a clean codebase. Avoid pre-baking half-finished auth scaffolding now.

---

## 3. Architectural Overview

### Three-graph composition

```
┌──────────────────────────────────────────────────────────────┐
│  PARENT GRAPH                                                 │
│  Owns: orchestration, ingestion, RAG indexing,                │
│        approval interrupts, exports                           │
│                                                                │
│  ├─ ingest_node                                                │
│  ├─ raw_rag_index_node                                         │
│  ├─ ANALYSER_SUBGRAPH ─── nested compiled graph               │
│  ├─ apply_review_1_edits_node  (interrupt_before)              │
│  ├─ DISCOVERY_SUBGRAPH ── nested compiled graph               │
│  ├─ route_review_2_node         (interrupt_before)              │
│  ├─ apply_review_2_edits_node                                   │
│  ├─ approved_rag_index_node                                     │
│  └─ artifact_export_node                                        │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────┐    ┌──────────────────────────┐
│  ANALYSER SUBGRAPH        │    │  DISCOVERY SUBGRAPH       │
│  ─────────────────        │    │  ──────────────────       │
│  score_node               │    │  prioritize_questions     │
│  enrich_node (conditional)│    │  generate_question_node   │
│  analyse_node             │    │  await_answer (interrupt) │
│                           │    │  process_answer_node      │
│                           │    │  finalize_doc_node        │
└──────────────────────────┘    └──────────────────────────┘
```

### Layered architecture

```
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND  (out of scope for this doc)                       │
└──────────────────┬───────────────────────────────────────────┘
                   │  REST + WebSocket  (no auth in this phase)
┌──────────────────▼───────────────────────────────────────────┐
│  API LAYER  (FastAPI + Python 3.11, runs on host)            │
│  File Upload · Stage Routing · WS Stream · Export            │
└──────────────────┬───────────────────────────────────────────┘
                   │  app.astream_events(...)
┌──────────────────▼───────────────────────────────────────────┐
│  AGENT LAYER  (LangGraph: parent + 2 subgraphs, on host)     │
│  Ingestion · Analyser · Discovery · RAG · Export             │
└──────────────────┬───────────────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────────────┐
│  DATA LAYER  (all in Docker containers on localhost)         │
│  PostgreSQL+pgvector  (structured + vectors + checkpointer)  │
│  Redis                (pub/sub for streaming)                │
│  MinIO                (S3-compatible — uploads + exports)    │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Complete Graph Topology

```
[START]
   │
   ▼
┌─────────────────────────────┐
│  ingest_node                │  PARENT
│  (parse all uploaded files) │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  raw_rag_index_node         │  PARENT
│  (chunk, embed, store with  │
│   TTL in working_chunks)    │
└────────────┬────────────────┘
             │
             ▼
╔═════════════════════════════╗
║  ANALYSER_SUBGRAPH          ║
║  ────────────────           ║
║  ┌────────────────────┐     ║
║  │  score_node        │     ║
║  └─────────┬──────────┘     ║
║            │                ║
║        ┌───┴───┐ conditional║
║      ≤5      ≥6             ║
║        │       │            ║
║        ▼       │            ║
║  ┌──────────┐  │            ║
║  │ enrich_  │  │            ║
║  │ node     │  │            ║
║  └─────┬────┘  │            ║
║        └───┬───┘            ║
║            ▼                ║
║  ┌────────────────────┐     ║
║  │  analyse_node      │     ║
║  └─────────┬──────────┘     ║
╚════════════│════════════════╝
             ▼
┌─────────────────────────────┐
│  apply_review_1_edits_node  │  PARENT
│  (interrupt_before)         │  ◄── INTERRUPT (human_review_1)
└────────────┬────────────────┘
             │
             ▼
╔═════════════════════════════╗
║  DISCOVERY_SUBGRAPH         ║
║  ─────────────────          ║
║  ┌────────────────────┐     ║
║  │ prioritize_        │     ║
║  │ questions_node     │     ║
║  └─────────┬──────────┘     ║
║            ▼                ║
║  ┌────────────────────┐ ◄─┐ ║
║  │ generate_question_ │   │ ║
║  │ node               │   │ ║
║  └─────────┬──────────┘   │ ║
║            ▼              │ ║
║  ┌────────────────────┐   │ ║   ◄── INTERRUPT
║  │ await_answer_node  │   │ ║       (inside subgraph)
║  │ (interrupt_before) │   │ ║
║  └─────────┬──────────┘   │ ║
║            ▼              │ ║
║  ┌────────────────────┐   │ ║
║  │ process_answer_    │   │ ║
║  │ node               │   │ ║
║  └─────────┬──────────┘   │ ║
║        ┌───┴───┐          │ ║
║       loop    done        │ ║
║        └───────┼──────────┘ ║
║                ▼            ║
║  ┌───────────────────┐      ║
║  │ finalize_doc_node │      ║
║  └─────────┬─────────┘      ║
╚════════════│════════════════╝
             ▼
┌─────────────────────────────┐
│  route_review_2_node        │  PARENT
│  (interrupt_before)         │  ◄── INTERRUPT (human_review_2)
└────────────┬────────────────┘
             │
        ┌────┼─────────────────────┐
        │    │                     │
   approved  edits             more_questions
        │    │                     │
        │    ▼                     │  loop back to
        │  ┌─────────────────┐     │  DISCOVERY_SUBGRAPH
        │  │ apply_review_2_ │     │
        │  │ edits_node      │     │
        │  └────────┬────────┘     │
        │           │              │
        │           └──► route_review_2_node (re-pause for re-review)
        ▼
┌─────────────────────────────┐
│  approved_rag_index_node    │  PARENT
│  (section-chunk, embed,     │
│   write permanent rows)     │
└────────────┬────────────────┘
             │
             ▼
┌─────────────────────────────┐
│  artifact_export_node       │  PARENT
│  (render PDF + DOCX,        │
│   upload, save S3 keys)     │
└────────────┬────────────────┘
             │
             ▼
           [END]
```

**Interrupts in this design:**
- `human_review_1` → implemented as `interrupt_before=["apply_review_1_edits_node"]`
- `await_answer` → implemented as `interrupt_before=["await_answer_node"]` inside Discovery subgraph
- `human_review_2` → implemented as `interrupt_before=["route_review_2_node"]`

Interrupts are configured on the **next deterministic node** that consumes user input, not as standalone nodes. Cleaner than no-op pause nodes.

---

## 5. State Schemas

State is the single most important contract in a LangGraph application. Every node reads from it and every node writes to it; if state is wrong, everything is wrong. This section explains not just *what* the schemas look like, but *why every key exists* and *how it flows through the graph*.

### 5.1 The mental model

LangGraph state is a single Python dict (typed via `TypedDict`) that flows through the graph. At each node:

1. The node receives the *current state*.
2. The node returns a *partial state dict* with only the keys it wants to update.
3. LangGraph merges the returned dict into the state. For keys with a reducer (e.g. `Annotated[list, add]`), the merge is append-style. For all other keys, it's overwrite-style.

This means:
- You don't need to read-modify-write the whole state in every node. Just return what you changed.
- Multiple nodes can append to the same list (e.g. `delta_changes`) without overwriting each other.
- State is checkpointed *after every node* by `PostgresSaver`. So if anything is in state, it survives a server restart and is available to resume from.

The corollary: **only put things in state that you genuinely need across nodes or across interrupts.** Heavy data (1536-dim embeddings, raw file bytes, full PDF text) goes in Postgres or MinIO; state holds only IDs and references.

### 5.2 Why three TypedDicts (not one)

We have three states: `GraphState` (parent), `AnalyserState` (Analyser subgraph), `DiscoveryState` (Discovery subgraph). All three live in `shared/state_types.py`.

**Reason 1 — Encapsulation.** When you're inside `analyse_node`, you should not be able to accidentally read `final_doc_pdf_s3_key`. It's not the Analyser's concern. By declaring a subgraph state that's a subset of the parent, you get compile-time-style isolation.

**Reason 2 — Automatic key mapping.** When LangGraph mounts a subgraph as a node in the parent, it maps state keys *by name overlap*. Keys in the parent state that aren't declared in the subgraph state are simply not exposed to the subgraph; they pass through untouched. Keys that *are* declared are visible and mutable. This is exactly what you want.

**Reason 3 — Future Stage 3/4 modularity.** When Stage 3 is added, it'll have its own `ArchitectureState` that overlaps with parent on `analyser_output`, `qa_history`, and a few new keys. Same pattern. Zero refactoring.

### 5.3 Sub-types — why each one exists

These are the building blocks. They're shared because both the parent and the subgraphs need to read/write the same shapes.

```python
from typing import TypedDict, Literal, Annotated
from operator import add

class ParsedSection(TypedDict):
    file_name: str
    section_heading: str | None      # extracted from doc structure
    page: int | None
    content_type: Literal["text", "table", "image_description"]
    content: str
    raw_image_ref: str | None        # S3 key if it's an image
```

**Why `ParsedSection` exists:** A document isn't a flat string. A 2-page PDF has headings, paragraphs, tables, and possibly diagrams. Each of those is a `ParsedSection`. Keeping them separate (instead of joining into one big string) lets the chunker treat tables as atomic and lets retrieval surface "the heading of the chunk that matched" — which dramatically improves Stage 1's grounding.

- `section_heading` improves retrieval relevance massively. A chunk under "Non-Functional Requirements" is more meaningful than the same text without that label.
- `content_type` lets `enrich_node` and `analyse_node` reason differently about a table (structured) versus a paragraph (prose).
- `raw_image_ref` is the S3 key of the original image. Even though the chunk text is the vision-LLM's *description* of the image, we keep the original around for display in the UI ("here's the diagram the agent referenced").

```python
class ParsedDocument(TypedDict):
    file_name: str
    file_type: str
    s3_key: str
    sections: list[ParsedSection]
```

**Why `ParsedDocument` exists:** Users can upload multiple files. Each gets its own ParsedDocument so that downstream we know which sections came from which file. The `s3_key` lets us re-fetch the original (e.g. for re-parsing if the first parse was bad).

```python
class ScoreBreakdown(TypedDict):
    functional_requirements: float    # 0-1
    business_logic: float
    existing_system: float
    target_audience: float
    architecture_context: float
    nfrs: float
    timeline_budget: float
    visual_assets: float
    weighted_total: float             # 0-10
    per_criterion_reasoning: dict[str, str]
```

**Why `ScoreBreakdown` exists:** Score isn't just one number — it's eight dimensions per the BRD. We keep all eight (plus the weighted total) because:
1. The conditional edge after `score_node` only needs `weighted_total`, but...
2. ...the `enrich_node` needs the *individual low-scoring criteria* to know what to enrich.
3. The UI shows the breakdown to the user so they understand *why* their doc was scored as it was.
4. `per_criterion_reasoning` is a one-sentence rationale per criterion, generated by the LLM. Keeping it lets the user see the reasoning, not just the number.

```python
class OpenQuestion(TypedDict):
    question_id: str
    question: str
    priority: Literal["high", "medium", "low"]
    blocked_decisions: list[str]      # which downstream things this gates
```

**Why `OpenQuestion` exists:** These are the questions the Analyser wants to ask. They're identified during Stage 1 but answered during Stage 2. They live in `analyser_output.open_questions`.

- `question_id` is durable. The same ID flows through `prioritize_questions_node`, `generate_question_node`, `await_answer_node`, into `qa_history`. It's also stored in `discovery_qa` table for audit. Don't generate it inside `generate_question_node`; generate it in `analyse_node` and reuse it.
- `priority` is set by `prioritize_questions_node`. The `generate_question_node` picks the highest-priority unanswered question each iteration.
- `blocked_decisions` tells `process_answer_node` *which fields of analyser_output might need to be patched* when this question is answered. It's the bridge between a Q&A and a state mutation.

```python
class FunctionalRequirement(TypedDict):
    req_id: str
    description: str
    moscow: Literal["must_have", "should_have", "good_to_have"]
    acceptance_hints: list[str]
    source: Literal["document", "enrichment", "qa"]
    source_ref: str | None            # chunk_id or question_id
```

**Why `FunctionalRequirement` exists:** Each requirement is a first-class object, not a bullet point in a string. Reasons:
- `req_id` is needed for stable references. When a Q&A in Stage 2 modifies a requirement, we patch by ID, not by text matching.
- `moscow` is BRD-mandated.
- `acceptance_hints` are short cues the LLM generates ("user can log in within 2 seconds", "supports 100 concurrent users") that Stage 4 will eventually expand into acceptance criteria. Storing them now costs nothing and is enormously useful later.
- `source` + `source_ref` is the audit trail: did this come from the original doc, from enrichment, or from a Q&A answer? When the user reviews, they can see the provenance and trust it (or not).

```python
class Risk(TypedDict):
    risk_id: str
    description: str
    category: Literal["technical", "business", "delivery"]
    severity: Literal["high", "medium", "low"]
    mitigation: str | None
```

**Why `Risk` exists:** Same reasoning as FunctionalRequirement — first-class object with stable ID for patching during Stage 2. `category` and `severity` are useful for filtering in the UI and for retrieval metadata in `requirement_nodes`. `mitigation` is optional because the LLM might not have a concrete mitigation for every risk; that's fine.

```python
class AnalyserResult(TypedDict):
    executive_summary: str
    project_overview: dict            # {objective, scope, out_of_scope}
    functional_requirements: list[FunctionalRequirement]
    risks: list[Risk]
    recommended_team: dict            # {roles, size, rationale}
    open_questions: list[OpenQuestion]
    completeness_score: ScoreBreakdown
    assumptions_made: list[dict]      # {assumption, source}
```

**Why `AnalyserResult` is the centerpiece of state:** This is the document. Stage 1 produces it; Stage 2 mutates it; the user reviews it; the final markdown is rendered from it; the post-approval RAG indexes it. Every other piece of state revolves around this one.

- `executive_summary` is short prose, rendered at the top of the final doc.
- `project_overview` is loosely structured (`{objective, scope, out_of_scope}`) because its sub-shape is stable; a `dict` is fine and avoids over-engineering with another TypedDict.
- `functional_requirements`, `risks`, `open_questions` are all lists of typed objects (not strings) so they can be patched by ID.
- `completeness_score` is embedded here (not just in `state.score`) because the final approved doc needs to carry its score forward — Stage 3+ may filter projects by completeness.
- `assumptions_made` is the explicit "this came from web search / inference, not the source doc" flag. Trustworthiness is a UX feature.

```python
class QAExchange(TypedDict):
    question_id: str
    question: str
    rationale: str                    # why this question matters
    options: list[str]
    answer: str | None
    selected_option_index: int | None
    status: Literal["answered", "deferred", "na", "unknown"]
    timestamp: str
    triggered_changes: list[dict]     # JSON patches applied
```

**Why `QAExchange` exists:** This is one round of the Stage 2 loop. It captures everything about that round so the audit trail is complete.

- `question_id` ties back to the original `OpenQuestion`.
- `rationale` is the user-visible "why this question matters" string; it's stored so re-runs can show the same explanation without regeneration.
- `options` (length 2-4) and `selected_option_index` together let us reconstruct *which option was picked* even if the user later changes their mind.
- `answer` is the canonical user-facing answer text — either the selected option's text or the free-text input.
- `status` is the four-state from §1: answered / deferred / na / unknown. This is what feeds analytics ("how many questions were unknown for this project?").
- `triggered_changes` is the list of JSON patches that *this answer caused*. Critical for audit: the user can see "answering this question changed Risk #2's severity from low to high".

```python
class DeltaChange(TypedDict):
    change_id: str
    source: Literal["enrichment", "qa", "user_edit"]
    source_ref: str                   # question_id, edit_id, etc.
    field_path: str                   # e.g. "risks[2].mitigation"
    old_value: str | None
    new_value: str
    timestamp: str
```

**Why `DeltaChange` exists:** Every mutation to `analyser_output` after its initial creation gets logged here. Three sources:
1. `enrichment` — `enrich_node` filled in a gap.
2. `qa` — a Stage 2 answer triggered a patch.
3. `user_edit` — the user edited something during `human_review_1` or `human_review_2`.

This list is `Annotated[list[DeltaChange], add]` because multiple nodes append to it. Without this, you can't reconstruct *how the document evolved*. Persisted to the `change_events` table at graph end.

```python
class StreamEvent(TypedDict):
    event_id: str
    type: str                         # node_start, token, tool_call, etc.
    node: str
    payload: dict
    timestamp: str
```

**Why `StreamEvent` exists:** Optional but useful — a log of every event emitted to the WebSocket. Lets you replay a session for debugging. If you find this is bloating state, you can move it to a separate Postgres table and remove it from state. For now, keep it; it's cheap.

### 5.4 Parent state — `GraphState` keys explained

```python
class GraphState(TypedDict):
    # ─── Identity ───
    project_id: str
    version: int
    thread_id: str

    # ─── Input ───
    raw_files: list[str]              # S3 keys
    additional_context: str

    # ─── Ingestion outputs ───
    parsed_documents: list[ParsedDocument]
    working_chunk_ids: list[str]

    # ─── Stage 1 outputs (mutated by Analyser subgraph) ───
    score: ScoreBreakdown | None
    needs_enrichment: bool
    analyser_output: AnalyserResult | None

    # ─── Stage 2 working state (mutated by Discovery subgraph) ───
    qa_history: Annotated[list[QAExchange], add]
    current_question: QAExchange | None
    questions_asked_count: int
    discovery_terminated: bool

    # ─── Final doc artifacts ───
    final_doc_markdown: str | None
    final_doc_pdf_s3_key: str | None
    final_doc_docx_s3_key: str | None

    # ─── Approval state ───
    review_1_status: Literal["pending", "edits_made", "approved"]
    review_2_status: Literal["pending", "edits_made", "more_questions", "approved"]
    user_edits_payload: dict | None

    # ─── Audit ───
    delta_changes: Annotated[list[DeltaChange], add]
    streaming_events: Annotated[list[StreamEvent], add]

    # ─── Config ───
    llm_config: dict[str, dict]       # keyed by agent_id (= node name)
```

#### Identity block

| Key | Why it exists |
|---|---|
| `project_id` | The primary key tying this run to the `projects` table. Used in every DB write, every S3 key, every WS channel name. Without it, nothing is correlated. |
| `version` | Supports re-runs (v1, v2, v3). Stage 3/4 changes will trigger v2 of the analyser doc later. By baking `version` into state from day 1, we never have to retrofit it. Every DB row gets `(project_id, version)` as a logical key. |
| `thread_id` | The LangGraph checkpointer uses this to identify the run. Conventionally `thread_id == project_id` for the first run, but a re-run might use a new thread to keep the v1 history intact. Decoupling them now leaves room for that. |

#### Input block

| Key | Why it exists |
|---|---|
| `raw_files` | List of S3 keys (in `bra-uploads`) for every file the user uploaded. The graph reads these, parses them, and the parsed text goes into `parsed_documents`. The S3 keys themselves are in state because re-running ingestion (e.g., on retry) needs to fetch them again. |
| `additional_context` | The free-text "anything else?" field from the upload UI. Treated as a synthetic ParsedDocument by `ingest_node`. It's preserved in state separately so the UI can show it as user-provided context (not as part of an uploaded file). |

#### Ingestion outputs

| Key | Why it exists |
|---|---|
| `parsed_documents` | The parsed sections from every file, fully expanded. This is the input to Stage 1's `score_node` and `analyse_node`. Lives in state because both Analyser and Discovery subgraphs need it; recomputing parsing on every node would be wasteful. |
| `working_chunk_ids` | List of UUIDs (not the chunks themselves) referencing rows in `working_chunks` pgvector table. Why IDs only? Because each chunk has a 1536-dim embedding (~6KB) and we'll have dozens. Storing them in state would bloat checkpoints to MBs. IDs are pointers; embeddings live in Postgres. |

#### Stage 1 outputs

| Key | Why it exists |
|---|---|
| `score` | Set by `score_node`. Required by `enrich_node` (to know which criteria to enrich) and by the conditional edge (`needs_enrichment`). Also surfaced to the UI so the user sees *why* the agent decided to enrich. |
| `needs_enrichment` | Derived from `score.weighted_total <= 5` but stored explicitly so the conditional edge function is trivial (just reads the bool). Could be computed inline in the edge function, but explicit is clearer. |
| `analyser_output` | The big one. Stage 1's deliverable. Mutated by Stage 2. Frozen at `human_review_2` approval. The single most important value in state. `None` until `analyse_node` populates it. |

#### Stage 2 working state

| Key | Why it exists |
|---|---|
| `qa_history` | Every Q&A round, appended. `Annotated[list, add]` because both `process_answer_node` and `generate_question_node` write to it (well, mostly process_answer; but the reducer is needed regardless because LangGraph merges parallel writes). Used by the next iteration's `generate_question_node` to avoid re-asking. |
| `current_question` | The one question currently in flight. Separate from `qa_history` because it's *unanswered* — it's the question the graph is waiting for the user to respond to. When the user responds, the resume handler updates this field's `answer`/`status`/etc., and `process_answer_node` then appends it to `qa_history` and clears `current_question`. |
| `questions_asked_count` | Simple integer counter. Used by the termination check (cap at 10). Could be derived from `len(qa_history)`, but storing it explicitly makes the cap check trivial and avoids surprises if `qa_history` ever has odd entries. |
| `discovery_terminated` | User-controlled flag. Set by `POST /api/projects/{id}/discovery/end`. The conditional edge after `process_answer_node` reads this to decide whether to loop or finalize. Lets the user stop early without waiting for the LLM to decide there are no more questions. |

#### Final doc artifacts

| Key | Why it exists |
|---|---|
| `final_doc_markdown` | The rendered final document. Produced by `finalize_doc_node` deterministically from `analyser_output`. Lives in state because `human_review_2` shows it to the user, and `apply_review_2_edits_node` may modify it (if the user edits the markdown directly). |
| `final_doc_pdf_s3_key`, `final_doc_docx_s3_key` | S3 keys for the rendered PDF and DOCX, set by `artifact_export_node`. Returned to the frontend via the `artifact_ready` event for download. |

#### Approval state

| Key | Why it exists |
|---|---|
| `review_1_status`, `review_2_status` | Tri/quad-state machines tracking where the user is in the approval flow. Set by the resume handler when the user POSTs to `/approve/{stage}`. Read by `apply_review_*_edits_node` and `route_review_2_node`. They're independent because Stage 1 has no "more_questions" option; only Stage 2 does. |
| `user_edits_payload` | The user's edits, if any. Cleared after being applied so it doesn't leak into the next interrupt. Shape varies by stage (Stage 1 edits structured AnalyserResult fields; Stage 2 might edit raw markdown OR structured fields). The shape is documented in the API spec. |

#### Audit

| Key | Why it exists |
|---|---|
| `delta_changes` | Append-only log of every mutation. Critical for compliance/audit and for the UI's "what changed?" feedback after each Stage 2 answer. |
| `streaming_events` | Append-only log of every WS event. Useful for debugging and for "replay this session". Optional — can be moved out of state if it bloats. |

#### Config

| Key | Why it exists |
|---|---|
| `llm_config` | Per-agent LLM configuration loaded from the `llm_configs` table at graph start. Keyed by node name (`"score_node"`, `"analyse_node"`, etc.). Lives in state so every node can read it via `get_llm(agent_id, state["llm_config"])` without doing its own DB lookup. Fetched once at graph entry (in a tiny preamble step or inside `ingest_node`). |

### 5.5 Analyser subgraph state — `AnalyserState`

```python
class AnalyserState(TypedDict):
    project_id: str
    version: int
    parsed_documents: list[ParsedDocument]
    working_chunk_ids: list[str]
    score: ScoreBreakdown | None
    needs_enrichment: bool
    analyser_output: AnalyserResult | None
    delta_changes: Annotated[list[DeltaChange], add]
    streaming_events: Annotated[list[StreamEvent], add]
    llm_config: dict[str, dict]
```

**What's included and why:**
- `project_id`, `version` — for logging, DB writes, S3 keys
- `parsed_documents` — primary input
- `working_chunk_ids` — for retrieval inside `enrich_node` and `analyse_node`
- `score`, `needs_enrichment` — Stage 1's intermediate outputs
- `analyser_output` — Stage 1's primary output
- `delta_changes` — `enrich_node` writes here when it fills a gap
- `streaming_events` — for streaming
- `llm_config` — per-agent LLM selection

**What's deliberately excluded:**
- `qa_history`, `current_question`, etc. — Discovery's concern, not Analyser's
- `final_doc_*`, `review_*_status` — out of scope for Stage 1
- `raw_files`, `additional_context` — already consumed by `ingest_node` (parent)

The subgraph cannot accidentally touch what isn't declared. Compile-time-style isolation.

### 5.6 Discovery subgraph state — `DiscoveryState`

```python
class DiscoveryState(TypedDict):
    project_id: str
    version: int
    working_chunk_ids: list[str]
    analyser_output: AnalyserResult       # mutated in place
    qa_history: Annotated[list[QAExchange], add]
    current_question: QAExchange | None
    questions_asked_count: int
    discovery_terminated: bool
    final_doc_markdown: str | None
    delta_changes: Annotated[list[DeltaChange], add]
    streaming_events: Annotated[list[StreamEvent], add]
    llm_config: dict[str, dict]
```

**What's included and why:**
- `analyser_output` — input AND output (mutated by `process_answer_node`)
- `working_chunk_ids` — for retrieval during question generation and answer processing
- `qa_history`, `current_question`, `questions_asked_count`, `discovery_terminated` — the loop's working state
- `final_doc_markdown` — written by `finalize_doc_node` at end of subgraph
- `delta_changes`, `streaming_events`, `llm_config` — same purposes as in Analyser

**What's deliberately excluded:**
- `parsed_documents` — Discovery doesn't re-parse; it works through retrieval over `working_chunk_ids`
- `score`, `needs_enrichment` — Stage 1's concern; Discovery only reads the resulting `analyser_output`
- `raw_files`, `review_*_status`, `final_doc_pdf_s3_key`, `final_doc_docx_s3_key` — parent's concerns

### 5.7 Schema rules (recap)

- **`Annotated[list, add]`** is mandatory for any list that multiple nodes append to. Without the reducer, every node's return value overwrites the list.
- **Reducers must match across parent and subgraph.** If parent says `Annotated[list, add]` and subgraph says plain `list`, the subgraph silently overwrites the parent's accumulated list. Always declare reducers identically across all three TypedDicts.
- **Sub-types must be imported from a shared module** (`shared/state_types.py`). Both parent and subgraphs import from there. No duplicating type definitions.
- **Vectors do NOT live in state.** `working_chunk_ids` is a list of UUIDs; the actual 1536-dim embeddings live in pgvector. This keeps checkpoints small and cheap.
- **Heavy strings (full PDF text) do NOT live in state.** They live in `documents.parsed_text_s3_key`. `parsed_documents` holds structured parsed sections, which are smaller and addressable, not raw concatenated text.
- **Don't add keys "just in case."** Every key in state survives every checkpoint write. Lean state = fast checkpoints = happy users.

---

## 6. Code Structure

```
bra_agents/
├── shared/
│   ├── state_types.py         # All TypedDicts + Pydantic schemas
│   ├── streaming.py           # Event publishing helpers
│   ├── llm_factory.py         # get_llm(agent_id) reads llm_configs table
│   └── postgres.py            # Connection pool, session helpers
│
├── ingestion/
│   ├── parser_router.py       # Routes by file extension
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   ├── pptx_parser.py
│   ├── xlsx_parser.py
│   ├── image_describer.py     # Vision LLM for embedded images
│   └── parsed_doc_schema.py
│
├── rag/
│   ├── chunker_recursive.py   # For raw docs (working_chunks)
│   ├── chunker_sectional.py   # For approved docs (requirement_nodes)
│   ├── embedder.py            # Batched embedding API calls
│   ├── pgvector_writer.py
│   ├── pgvector_retriever.py  # Hybrid: vector + tsvector + RRF
│   └── retrieval_tool.py      # LangChain tool wrapper for nodes
│
├── analyser/
│   ├── __init__.py            # Exports build_analyser_subgraph()
│   ├── graph.py               # The compiled subgraph
│   ├── state.py               # AnalyserState
│   ├── nodes/
│   │   ├── score.py
│   │   ├── enrich.py
│   │   └── analyse.py
│   ├── prompts/
│   │   ├── score_prompt.py
│   │   ├── enrich_prompt.py
│   │   └── analyse_prompt.py
│   └── schemas.py             # Pydantic for structured outputs
│
├── discovery/
│   ├── __init__.py            # Exports build_discovery_subgraph()
│   ├── graph.py
│   ├── state.py               # DiscoveryState
│   ├── nodes/
│   │   ├── prioritize.py
│   │   ├── generate_question.py
│   │   ├── await_answer.py    # interrupt placeholder
│   │   ├── process_answer.py
│   │   └── finalize_doc.py
│   ├── prompts/
│   │   ├── prioritize_prompt.py
│   │   ├── generate_prompt.py
│   │   └── process_answer_prompt.py
│   └── schemas.py
│
├── parent/
│   ├── graph.py               # build_parent_graph() — composes everything
│   ├── nodes/
│   │   ├── ingest.py
│   │   ├── raw_rag_index.py
│   │   ├── apply_review_1_edits.py
│   │   ├── route_review_2.py
│   │   ├── apply_review_2_edits.py
│   │   ├── approved_rag_index.py
│   │   └── artifact_export.py
│   └── interrupts.py          # Interrupt config
│
├── tools/
│   ├── web_search.py          # Used only inside enrich_node
│   ├── json_patcher.py        # Used inside process_answer_node
│   └── jinja_renderer.py      # For finalize_doc_node
│
├── api/
│   ├── main.py                # FastAPI app
│   ├── routes/
│   │   ├── projects.py
│   │   ├── documents.py
│   │   ├── discovery.py       # POST /discovery/answer
│   │   ├── reviews.py         # POST /approve/{stage}
│   │   └── exports.py
│   └── websocket.py           # /ws/projects/{id}/stream
│
├── runner/
│   ├── graph_runner.py        # Wraps app.astream_events for the API
│   ├── checkpointer.py        # PostgresSaver setup
│   └── event_publisher.py     # Pushes events to Redis pub/sub
│
└── tests/
    ├── unit/
    ├── integration/
    │   ├── test_analyser_subgraph.py
    │   ├── test_discovery_subgraph.py
    │   └── test_parent_e2e.py
    └── fixtures/
        └── sample_brds/
```

---

## 7. Analyser Subgraph

```python
# bra_agents/analyser/graph.py

from langgraph.graph import StateGraph, START, END
from .state import AnalyserState
from .nodes.score import score_node
from .nodes.enrich import enrich_node
from .nodes.analyse import analyse_node


def _route_after_score(state: AnalyserState) -> str:
    return "enrich_node" if state["needs_enrichment"] else "analyse_node"


def build_analyser_subgraph():
    """Build and compile the Analyser subgraph.

    Returns a compiled graph that can be added as a node to the parent.
    No internal interrupts — runs end-to-end on invoke.
    No checkpointer — inherits parent's checkpointer when mounted.
    """
    g = StateGraph(AnalyserState)

    g.add_node("score_node", score_node)
    g.add_node("enrich_node", enrich_node)
    g.add_node("analyse_node", analyse_node)

    g.add_edge(START, "score_node")
    g.add_conditional_edges(
        "score_node",
        _route_after_score,
        {"enrich_node": "enrich_node", "analyse_node": "analyse_node"},
    )
    g.add_edge("enrich_node", "analyse_node")
    g.add_edge("analyse_node", END)

    return g.compile()
```

**Critical:** Do NOT pass a checkpointer when compiling the subgraph. It inherits the parent's checkpointer when mounted. Compiling with `compile(checkpointer=...)` here causes silent state corruption.

---

## 8. Discovery Subgraph

```python
# bra_agents/discovery/graph.py

from langgraph.graph import StateGraph, START, END
from .state import DiscoveryState
from .nodes.prioritize import prioritize_questions_node
from .nodes.generate_question import generate_question_node
from .nodes.await_answer import await_answer_node
from .nodes.process_answer import process_answer_node
from .nodes.finalize_doc import finalize_doc_node


def _route_after_process(state: DiscoveryState) -> str:
    """Decide whether to loop for another question or finalize."""
    if state["discovery_terminated"]:
        return "finalize_doc_node"
    if state["questions_asked_count"] >= 10:
        return "finalize_doc_node"
    if state["current_question"] is None:
        return "finalize_doc_node"

    asked_ids = {qa["question_id"] for qa in state["qa_history"]}
    unresolved = [
        q for q in state["analyser_output"]["open_questions"]
        if q["question_id"] not in asked_ids
    ]
    if not unresolved:
        return "finalize_doc_node"
    return "generate_question_node"


def build_discovery_subgraph():
    g = StateGraph(DiscoveryState)

    g.add_node("prioritize_questions_node", prioritize_questions_node)
    g.add_node("generate_question_node", generate_question_node)
    g.add_node("await_answer_node", await_answer_node)
    g.add_node("process_answer_node", process_answer_node)
    g.add_node("finalize_doc_node", finalize_doc_node)

    g.add_edge(START, "prioritize_questions_node")
    g.add_edge("prioritize_questions_node", "generate_question_node")
    g.add_edge("generate_question_node", "await_answer_node")
    g.add_edge("await_answer_node", "process_answer_node")
    g.add_conditional_edges(
        "process_answer_node",
        _route_after_process,
        {
            "generate_question_node": "generate_question_node",
            "finalize_doc_node": "finalize_doc_node",
        },
    )
    g.add_edge("finalize_doc_node", END)

    return g.compile(interrupt_before=["await_answer_node"])
```

**`await_answer_node` is a no-op pass-through:**

```python
# bra_agents/discovery/nodes/await_answer.py
def await_answer_node(state: DiscoveryState) -> dict:
    """Placeholder. Graph interrupts BEFORE this node.
    On resume via Command(resume=...), the answer is injected into
    current_question by the resume handler, then this node forwards
    state unchanged.
    """
    return {}
```

**Termination conditions** (any one triggers exit from loop):
- `discovery_terminated == True` (user clicked "I'm done")
- `questions_asked_count >= 10` (hard cap)
- `current_question is None` (LLM signaled no more high-value questions)
- All `open_questions` are resolved or in `qa_history`

---

## 9. Parent Graph

```python
# bra_agents/parent/graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from shared.state_types import GraphState
from analyser import build_analyser_subgraph
from discovery import build_discovery_subgraph
from .nodes.ingest import ingest_node
from .nodes.raw_rag_index import raw_rag_index_node
from .nodes.apply_review_1_edits import apply_review_1_edits_node
from .nodes.route_review_2 import route_review_2_node
from .nodes.apply_review_2_edits import apply_review_2_edits_node
from .nodes.approved_rag_index import approved_rag_index_node
from .nodes.artifact_export import artifact_export_node


def _route_after_review_2(state: GraphState) -> str:
    status = state["review_2_status"]
    if status == "approved":
        return "approved_rag_index_node"
    if status == "edits_made":
        return "apply_review_2_edits_node"
    if status == "more_questions":
        return "discovery_subgraph"
    return "approved_rag_index_node"


def build_parent_graph(checkpointer: PostgresSaver):
    g = StateGraph(GraphState)

    # Mount subgraphs as nodes
    analyser_subgraph = build_analyser_subgraph()
    discovery_subgraph = build_discovery_subgraph()
    g.add_node("analyser_subgraph", analyser_subgraph)
    g.add_node("discovery_subgraph", discovery_subgraph)

    # Parent's own nodes
    g.add_node("ingest_node", ingest_node)
    g.add_node("raw_rag_index_node", raw_rag_index_node)
    g.add_node("apply_review_1_edits_node", apply_review_1_edits_node)
    g.add_node("route_review_2_node", route_review_2_node)
    g.add_node("apply_review_2_edits_node", apply_review_2_edits_node)
    g.add_node("approved_rag_index_node", approved_rag_index_node)
    g.add_node("artifact_export_node", artifact_export_node)

    # Linear backbone
    g.add_edge(START, "ingest_node")
    g.add_edge("ingest_node", "raw_rag_index_node")
    g.add_edge("raw_rag_index_node", "analyser_subgraph")
    g.add_edge("analyser_subgraph", "apply_review_1_edits_node")
    g.add_edge("apply_review_1_edits_node", "discovery_subgraph")
    g.add_edge("discovery_subgraph", "route_review_2_node")

    g.add_conditional_edges(
        "route_review_2_node",
        _route_after_review_2,
        {
            "approved_rag_index_node": "approved_rag_index_node",
            "apply_review_2_edits_node": "apply_review_2_edits_node",
            "discovery_subgraph": "discovery_subgraph",
        },
    )

    # Edits loop back for re-review
    g.add_edge("apply_review_2_edits_node", "route_review_2_node")

    g.add_edge("approved_rag_index_node", "artifact_export_node")
    g.add_edge("artifact_export_node", END)

    return g.compile(
        checkpointer=checkpointer,
        interrupt_before=[
            "apply_review_1_edits_node",   # human_review_1
            "route_review_2_node",         # human_review_2
        ],
    )
```

**Key composition behaviors:**
- LangGraph maps state keys by name overlap. When the parent invokes `analyser_subgraph`, only `AnalyserState` keys are exposed to it. State writes flow back automatically.
- The parent's checkpointer wraps the subgraphs. Inner interrupts (Discovery's `await_answer_node`) are still routed through the parent thread.
- Edits loop (`apply_review_2_edits_node` → `route_review_2_node`) means after applying edits, the graph re-pauses at `human_review_2` so the user can approve the edited version.

---

## 10. Node-by-Node Specification

Each node is presented as a blueprint with five parts:

1. **Purpose** — what this node does in plain English
2. **Contract** — exact input keys read, output keys written, side effects
3. **Pseudocode** — step-by-step implementation outline (close to real Python, not full code)
4. **Streaming events** — what the node emits to the WebSocket
5. **Error handling** — how it fails gracefully

The pseudocode is meant to be a faithful blueprint a developer can implement directly. It uses real library names and real method signatures where possible.

---

### 10.1 ingest_node (parent, tool node)

**Purpose.** Read every uploaded file from MinIO, parse it into structured `ParsedSection` objects, describe any embedded images via vision LLM, and emit a list of `ParsedDocument`s. Also fold the user's "additional context" textarea into a synthetic ParsedDocument so it's treated equivalently to uploaded content.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `raw_files` | List of S3 keys in `bra-uploads` bucket |
| Reads | `additional_context` | Optional free-text from upload UI |
| Writes | `parsed_documents` | List of fully-parsed documents |
| Side effect | Updates `documents` DB row with `parsed_text_s3_key` (cached parsed text uploaded back to MinIO) |
| Side effect | Emits streaming events |

**Pseudocode.**

```python
def ingest_node(state: GraphState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "ingest_node"})

    parsed_documents = []
    failed_files = []

    for s3_key in state["raw_files"]:
        try:
            publisher.emit("tool_call", {
                "node": "ingest_node",
                "tool": "parser",
                "input_summary": f"Parsing {s3_key}"
            })

            # 1. Download from MinIO to a temp file
            local_path = download_from_minio(
                bucket=settings.S3_BUCKET_UPLOADS,
                key=s3_key
            )

            # 2. Route by extension to the right parser
            extension = Path(local_path).suffix.lower()
            parser = PARSER_REGISTRY[extension]   # pdf, docx, pptx, xlsx
            sections = parser.parse(local_path)
            # Each section is a partial ParsedSection — content_type set,
            # but raw_image_ref still needs vision-LLM description for images.

            # 3. For any image-type sections, get a vision LLM description
            for section in sections:
                if section["content_type"] == "image_description":
                    image_bytes = read_image(section["raw_image_ref"])
                    section["content"] = describe_image_with_vision_llm(
                        image_bytes,
                        agent_id="ingest_node",
                        llm_config=state["llm_config"],
                    )

            # 4. Build the ParsedDocument
            parsed_doc = ParsedDocument(
                file_name=os.path.basename(s3_key),
                file_type=extension.lstrip('.'),
                s3_key=s3_key,
                sections=sections,
            )
            parsed_documents.append(parsed_doc)

            # 5. Cache parsed text back to MinIO for re-runs / debugging
            parsed_text = "\n\n".join(s["content"] for s in sections)
            parsed_text_key = f"{state['project_id']}/parsed/{s3_key}.txt"
            upload_to_minio(
                bucket=settings.S3_BUCKET_UPLOADS,
                key=parsed_text_key,
                body=parsed_text.encode(),
            )
            update_document_row(
                project_id=state["project_id"],
                s3_key=s3_key,
                parsed_text_s3_key=parsed_text_key,
            )

        except Exception as e:
            failed_files.append({"s3_key": s3_key, "error": str(e)})
            log.error(f"Failed to parse {s3_key}: {e}")
            publisher.emit("tool_complete", {
                "node": "ingest_node",
                "tool": "parser",
                "status": "failed",
                "error": str(e),
            })
            continue

    # 6. Synthesize the additional_context as its own ParsedDocument
    if state.get("additional_context"):
        parsed_documents.append(ParsedDocument(
            file_name="user_context",
            file_type="text",
            s3_key="",
            sections=[ParsedSection(
                file_name="user_context",
                section_heading=None,
                page=None,
                content_type="text",
                content=state["additional_context"],
                raw_image_ref=None,
            )],
        ))

    publisher.emit("node_complete", {
        "node": "ingest_node",
        "files_parsed": len(parsed_documents),
        "files_failed": len(failed_files),
    })

    return {"parsed_documents": parsed_documents}
```

**Streaming events.**
- `node_start` at entry
- `tool_call` per file being parsed
- `tool_complete` per file (with status: success/failed)
- `node_complete` with summary counts

**Error handling.**
- Per-file try/except: one bad file doesn't kill the whole ingestion.
- Failed files are logged and reported in the `node_complete` event so the UI can show "1 of 3 files failed".
- If *all* files fail, downstream `score_node` will see empty `parsed_documents`. That's an upstream user error (they uploaded only broken files); let it surface naturally — `score_node` will return a near-zero score and `enrich_node` will run.

---

### 10.2 raw_rag_index_node (parent, tool node)

**Purpose.** Take the parsed documents, chunk them with the recursive splitter, embed each chunk, and bulk-insert into `working_chunks` table with TTL. Returns the list of chunk UUIDs into state.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `parsed_documents` | |
| Reads | `project_id`, `version` | For metadata + filtering |
| Writes | `working_chunk_ids` | UUIDs, not embeddings |
| Side effect | Inserts rows into `working_chunks` table |

**Pseudocode.**

```python
def raw_rag_index_node(state: GraphState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "raw_rag_index_node"})

    # 1. Build a list of "chunk candidates" from all parsed sections
    chunk_candidates = []
    for doc in state["parsed_documents"]:
        for section in doc["sections"]:
            if section["content_type"] == "table":
                # Tables stay intact — one chunk per table
                chunk_candidates.append({
                    "text": section["content"],
                    "metadata": {
                        "file_name": doc["file_name"],
                        "page": section["page"],
                        "section_heading": section["section_heading"],
                        "content_type": "table",
                        "raw_image_ref": None,
                    }
                })
            elif section["content_type"] == "image_description":
                # Image descriptions become one chunk each
                chunk_candidates.append({
                    "text": section["content"],
                    "metadata": {
                        "file_name": doc["file_name"],
                        "page": section["page"],
                        "section_heading": section["section_heading"],
                        "content_type": "image_description",
                        "raw_image_ref": section["raw_image_ref"],
                    }
                })
            else:
                # Text gets recursive-split with semantic boundaries
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    separators=["\n\n", "\n", ". ", " ", ""],
                )
                sub_chunks = splitter.split_text(section["content"])
                for sc in sub_chunks:
                    chunk_candidates.append({
                        "text": sc,
                        "metadata": {
                            "file_name": doc["file_name"],
                            "page": section["page"],
                            "section_heading": section["section_heading"],
                            "content_type": "text",
                            "raw_image_ref": None,
                        }
                    })

    # 2. Batch-embed
    BATCH_SIZE = 100
    embeddings = []
    for i in range(0, len(chunk_candidates), BATCH_SIZE):
        batch = chunk_candidates[i:i + BATCH_SIZE]
        batch_embeddings = embedding_client.embed_batch(
            [c["text"] for c in batch]
        )
        embeddings.extend(batch_embeddings)
        publisher.emit("progress", {
            "node": "raw_rag_index_node",
            "completed": i + len(batch),
            "total": len(chunk_candidates),
        })

    # 3. Bulk insert
    chunk_ids = []
    rows = []
    expires_at = datetime.utcnow() + timedelta(days=30)
    for candidate, emb in zip(chunk_candidates, embeddings):
        chunk_id = uuid4()
        chunk_ids.append(str(chunk_id))
        rows.append({
            "chunk_id": chunk_id,
            "project_id": state["project_id"],
            "version": state["version"],
            "text": candidate["text"],
            "metadata": candidate["metadata"],
            "embedding": emb,
            "expires_at": expires_at,
        })

    bulk_insert("working_chunks", rows)

    publisher.emit("node_complete", {
        "node": "raw_rag_index_node",
        "chunks_indexed": len(chunk_ids),
    })

    return {"working_chunk_ids": chunk_ids}
```

**Streaming events.**
- `node_start`
- `progress` after each batch (driven by BATCH_SIZE)
- `node_complete` with chunk count

**Error handling.**
- If the embedding API throws, retry the batch with exponential backoff (3 attempts).
- If a batch still fails after retries, log and skip *that batch only* — partial indexing is better than no indexing.
- Embedding-API key missing: hard fail at startup, not at this node.

---

### 10.3 score_node (analyser subgraph, LLM node)

**Purpose.** Read the parsed documents and produce a weighted score across the 8 BRD criteria. Set `needs_enrichment` flag based on whether the score is too low.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `parsed_documents` | Full text — fits in context for 2-3 page docs |
| Reads | `llm_config` | For per-agent LLM selection |
| Writes | `score: ScoreBreakdown` | All 8 dimensions + weighted total + reasoning |
| Writes | `needs_enrichment: bool` | True if `weighted_total <= 5` |

**Pseudocode.**

```python
def score_node(state: AnalyserState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "score_node"})

    # 1. Concatenate all parsed text into a single context string
    full_text = "\n\n".join(
        f"# {section['section_heading'] or 'Untitled'}\n{section['content']}"
        for doc in state["parsed_documents"]
        for section in doc["sections"]
    )

    # 2. Get the LLM via factory (per-agent config)
    llm = get_llm("score_node", state["llm_config"])
    structured_llm = llm.with_structured_output(ScoreBreakdownSchema)

    # 3. Build the prompt — chain-of-thought per criterion
    prompt = SCORE_PROMPT.format(
        document_text=full_text,
        criteria=SCORING_CRITERIA_DESCRIPTIONS,
        weights=SCORING_WEIGHTS,
    )

    # 4. Invoke (streams tokens via callbacks)
    score = structured_llm.invoke(prompt)
    score_dict = score.model_dump()

    # 5. Compute weighted total deterministically (don't trust the LLM's math)
    weighted_total = sum(
        score_dict[criterion] * weight
        for criterion, weight in SCORING_WEIGHTS.items()
    ) * 10  # scale 0-1 → 0-10
    score_dict["weighted_total"] = round(weighted_total, 2)

    needs_enrichment = score_dict["weighted_total"] <= 5.0

    publisher.emit("score_ready", {
        "node": "score_node",
        "score": score_dict,
        "needs_enrichment": needs_enrichment,
    })
    publisher.emit("node_complete", {
        "node": "score_node",
        "weighted_total": score_dict["weighted_total"],
    })

    return {
        "score": score_dict,
        "needs_enrichment": needs_enrichment,
    }
```

**Scoring criteria (from BRD):**

| Criterion | Weight |
|---|---|
| Functional Requirements | 20% |
| Business Logic / Rules | 15% |
| Existing Product / System Info | 15% |
| Target Audience / Users | 10% |
| Architecture / Technical Context | 15% |
| Non-Functional Requirements | 10% |
| Timeline / Budget Signals | 10% |
| Visual Assets (Diagrams/Flows) | 5% |

**Streaming events.**
- `node_start`
- `token` events during LLM streaming (auto-emitted by LangChain callbacks)
- `score_ready` with full breakdown
- `node_complete`

**Error handling.**
- LLM timeout: retry once with shorter prompt (truncate `parsed_documents` to first 8K tokens).
- LLM returns malformed JSON: Pydantic catches it; retry with a "fix the JSON" prompt.
- Persistent failure: emit `error` event and re-raise. Parent graph will surface to user.

---

### 10.4 enrich_node (analyser subgraph, LLM node, conditional)

**Purpose.** When the document scored low (≤5), fill in the gaps. Use raw RAG to confirm what's actually in the doc, then web search to find industry norms for missing pieces. Every inference gets logged as an assumption.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `parsed_documents`, `score`, `working_chunk_ids` | |
| Writes | `parsed_documents` | Adds synthetic enrichment sections |
| Writes | `delta_changes` (append) | Logs each enrichment as a delta |

**Pseudocode.**

```python
def enrich_node(state: AnalyserState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "enrich_node"})

    # 1. Identify low-scoring criteria (those below 0.6 in the breakdown)
    low_criteria = [
        criterion for criterion, val in state["score"].items()
        if isinstance(val, (int, float)) and val < 0.6
        and criterion != "weighted_total"
    ]

    if not low_criteria:
        # Shouldn't happen if we routed here, but be defensive
        publisher.emit("node_complete", {"node": "enrich_node", "skipped": True})
        return {}

    # 2. For each low criterion, build a query and retrieve from raw RAG
    enrichment_sections = []
    new_deltas = []
    web_search_count = 0
    WEB_SEARCH_CAP = 5

    llm = get_llm("enrich_node", state["llm_config"])
    web_search_tool = WebSearchTool()
    rag_retriever = RawRagRetriever(
        project_id=state["project_id"],
        version=state["version"],
    )

    for criterion in low_criteria:
        publisher.emit("tool_call", {
            "node": "enrich_node",
            "tool": "rag_retriever",
            "input_summary": f"Looking for {criterion} info in source doc",
        })
        # 2a. Try the source doc first
        rag_results = rag_retriever.retrieve(
            query=CRITERION_QUERY_TEMPLATES[criterion],
            k=3,
        )

        # 2b. If source doc has nothing, web-search for industry norms
        web_findings = []
        if all_results_low_relevance(rag_results) and web_search_count < WEB_SEARCH_CAP:
            publisher.emit("tool_call", {
                "node": "enrich_node",
                "tool": "web_search",
                "input_summary": f"Industry norms for {criterion}",
            })
            web_findings = web_search_tool.search(
                query=f"typical {criterion} for {infer_project_type(state)} 2026",
                max_results=3,
            )
            web_search_count += 1

        # 2c. Ask LLM to synthesize an enrichment paragraph + assumption flag
        synthesis_prompt = ENRICH_PROMPT.format(
            criterion=criterion,
            source_doc_findings=rag_results,
            web_findings=web_findings,
        )
        enrichment = llm.invoke(synthesis_prompt)

        enrichment_sections.append(ParsedSection(
            file_name="enrichment",
            section_heading=f"Inferred: {criterion}",
            page=None,
            content_type="text",
            content=enrichment.content,
            raw_image_ref=None,
        ))

        new_deltas.append(DeltaChange(
            change_id=str(uuid4()),
            source="enrichment",
            source_ref=criterion,
            field_path=f"parsed_documents[enrichment].{criterion}",
            old_value=None,
            new_value=enrichment.content[:200],   # snippet for audit
            timestamp=now_iso(),
        ))

    # 3. Append enrichment as a new synthetic ParsedDocument
    enriched_docs = state["parsed_documents"] + [ParsedDocument(
        file_name="enrichment",
        file_type="synthetic",
        s3_key="",
        sections=enrichment_sections,
    )]

    publisher.emit("node_complete", {
        "node": "enrich_node",
        "criteria_enriched": len(low_criteria),
        "web_searches_used": web_search_count,
    })

    return {
        "parsed_documents": enriched_docs,
        "delta_changes": new_deltas,
    }
```

**Streaming events.**
- `node_start`
- `tool_call` per RAG retrieval and per web search
- `node_complete` with counts of criteria enriched and searches used

**Error handling.**
- Web search timeout: skip web findings for that criterion, fall back to RAG-only synthesis.
- Web search cap (5): once hit, no more web searches this run; remaining criteria use RAG-only.
- LLM synthesis failure: log and skip *that criterion only*. Don't kill the whole enrichment.

---

### 10.5 analyse_node (analyser subgraph, LLM node)

**Purpose.** The big one. Read all the (possibly enriched) parsed content, retrieve relevant chunks for grounding, and produce a complete `AnalyserResult` with all 8 sections — exec summary, project overview, MoSCoW-classified functional requirements, risks, recommended team, open questions, completeness score, assumptions made.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `parsed_documents`, `score`, `working_chunk_ids` | |
| Reads | `llm_config["analyse_node"]` | Bigger model recommended |
| Writes | `analyser_output: AnalyserResult` | The whole structured output |

**Pseudocode.**

```python
def analyse_node(state: AnalyserState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "analyse_node"})

    # 1. Build the full context — all parsed sections
    full_context = format_parsed_documents(state["parsed_documents"])

    # 2. Optionally retrieve relevant chunks for grounding
    # (For 2-3 page docs this is redundant, but it's cheap and future-proofs.)
    rag_retriever = RawRagRetriever(
        project_id=state["project_id"],
        version=state["version"],
    )
    grounding_chunks = rag_retriever.retrieve(
        query="key requirements, business logic, risks, target users",
        k=10,
    )

    # 3. Get the LLM (typically Claude Opus or GPT-4o for this node)
    llm = get_llm("analyse_node", state["llm_config"])
    structured_llm = llm.with_structured_output(AnalyserResultSchema)

    # 4. Build the analysis prompt
    prompt = ANALYSE_PROMPT.format(
        document_context=full_context,
        grounding_chunks=grounding_chunks,
        score_breakdown=state["score"],
    )

    # 5. Invoke — tokens stream automatically via callbacks
    analyser_result = structured_llm.invoke(prompt)
    result_dict = analyser_result.model_dump()

    # 6. Post-process: assign stable IDs to requirements, risks, questions
    for i, req in enumerate(result_dict["functional_requirements"]):
        if not req.get("req_id"):
            req["req_id"] = f"FR-{i+1:03d}"
    for i, risk in enumerate(result_dict["risks"]):
        if not risk.get("risk_id"):
            risk["risk_id"] = f"RISK-{i+1:03d}"
    for i, q in enumerate(result_dict["open_questions"]):
        if not q.get("question_id"):
            q["question_id"] = f"q_{uuid4().hex[:8]}"

    # 7. Embed the score we computed earlier
    result_dict["completeness_score"] = state["score"]

    publisher.emit("analysis_ready", {
        "node": "analyse_node",
        "analyser_output": result_dict,
    })
    publisher.emit("node_complete", {"node": "analyse_node"})

    return {"analyser_output": result_dict}
```

**Streaming events.**
- `node_start`
- `token` events during LLM streaming (the user sees the report being written live)
- `analysis_ready` with full AnalyserResult
- `node_complete`

**Error handling.**
- Pydantic validation failure: retry once with explicit "your previous output failed validation: <error>; please fix" prompt.
- Token limit exceeded: truncate `parsed_documents` to top-relevance chunks via RAG; retry.
- Persistent failure: emit `error` event and re-raise.

---

### 10.6 apply_review_1_edits_node (parent, deterministic)

**Purpose.** After `human_review_1` interrupt resumes with the user's edits, apply those edits to `analyser_output` and log every change in `delta_changes`. If the user just approved without edits, this is a no-op pass-through.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `analyser_output`, `user_edits_payload`, `review_1_status` | |
| Writes | `analyser_output` | Mutated with edits |
| Writes | `delta_changes` (append) | One per edit |
| Writes | `user_edits_payload: None` | Cleared after application |

**Pseudocode.**

```python
def apply_review_1_edits_node(state: GraphState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "apply_review_1_edits_node"})

    # 1. If user just approved, pass through
    if state["review_1_status"] == "approved" or not state.get("user_edits_payload"):
        publisher.emit("node_complete", {
            "node": "apply_review_1_edits_node",
            "edits_applied": 0,
        })
        return {"user_edits_payload": None}

    # 2. user_edits_payload is a list of JSON patches per RFC 6902
    # Example: [{"op": "replace", "path": "/risks/2/severity", "value": "high"}]
    patches = state["user_edits_payload"]["patches"]
    analyser_output = deepcopy(state["analyser_output"])

    new_deltas = []
    for patch in patches:
        path = patch["path"]
        old_value = jsonpointer.resolve(analyser_output, path, default=None)

        analyser_output = jsonpatch.JsonPatch([patch]).apply(analyser_output)

        new_deltas.append(DeltaChange(
            change_id=str(uuid4()),
            source="user_edit",
            source_ref="review_1",
            field_path=path,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(patch.get("value", "")),
            timestamp=now_iso(),
        ))

    publisher.emit("node_complete", {
        "node": "apply_review_1_edits_node",
        "edits_applied": len(patches),
    })

    return {
        "analyser_output": analyser_output,
        "delta_changes": new_deltas,
        "user_edits_payload": None,    # clear it
    }
```

**Streaming events.**
- `node_start`, `node_complete` with edit count

**Error handling.**
- Invalid JSON path: log and skip that single patch; continue with others.
- Whole payload malformed: emit error event, re-raise.

---

### 10.7 prioritize_questions_node (discovery subgraph, LLM node)

**Purpose.** Given the open questions in `analyser_output`, sort them by downstream impact. Cheap LLM call. Sets `priority` field on each question.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `analyser_output.open_questions` | |
| Writes | `analyser_output` | Same questions, sorted with priority |

**Pseudocode.**

```python
def prioritize_questions_node(state: DiscoveryState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "prioritize_questions_node"})

    open_questions = state["analyser_output"]["open_questions"]
    if not open_questions:
        publisher.emit("node_complete", {
            "node": "prioritize_questions_node",
            "questions_count": 0,
        })
        return {}

    llm = get_llm("prioritize_questions_node", state["llm_config"])
    structured_llm = llm.with_structured_output(PrioritizedQuestionsSchema)

    prompt = PRIORITIZE_PROMPT.format(
        open_questions=open_questions,
        analyser_output=state["analyser_output"],
    )
    result = structured_llm.invoke(prompt)

    # Result is the same questions with priority field updated.
    # We trust the LLM's order but verify all original IDs are present.
    new_questions = result.model_dump()["questions"]
    assert {q["question_id"] for q in new_questions} == \
           {q["question_id"] for q in open_questions}

    new_analyser = deepcopy(state["analyser_output"])
    new_analyser["open_questions"] = new_questions

    publisher.emit("node_complete", {
        "node": "prioritize_questions_node",
        "questions_count": len(new_questions),
    })

    return {"analyser_output": new_analyser}
```

**Streaming events.** `node_start`, `node_complete`. No tokens — too quick to bother.

**Error handling.** If LLM drops a question or invents a new ID, fall back to original order and log warning.

---

### 10.8 generate_question_node (discovery subgraph, LLM node, in loop)

**Purpose.** Pick the next most-impactful unanswered question. Generate it with rationale + 2-4 options. Or signal termination.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `analyser_output`, `qa_history`, `questions_asked_count`, `working_chunk_ids` | |
| Writes | `current_question: QAExchange` (or None for terminate) | |
| Writes | `questions_asked_count` (incremented) | |

**Pseudocode.**

```python
def generate_question_node(state: DiscoveryState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "generate_question_node"})

    # 1. Hard cap check
    if state["questions_asked_count"] >= 10:
        publisher.emit("node_complete", {
            "node": "generate_question_node",
            "terminated": True,
            "reason": "Hard cap reached (10 questions)",
        })
        return {"current_question": None}

    # 2. Compute remaining unanswered questions
    asked_ids = {qa["question_id"] for qa in state["qa_history"]}
    unanswered = [
        q for q in state["analyser_output"]["open_questions"]
        if q["question_id"] not in asked_ids
    ]
    if not unanswered:
        publisher.emit("node_complete", {
            "node": "generate_question_node",
            "terminated": True,
            "reason": "No unanswered questions",
        })
        return {"current_question": None}

    # 3. Retrieve context from raw RAG to ground question generation
    rag_retriever = RawRagRetriever(
        project_id=state["project_id"],
        version=state["version"],
    )
    relevant_chunks = rag_retriever.retrieve(
        query=" ".join(q["question"] for q in unanswered[:3]),
        k=5,
    )

    # 4. LLM call with structured output
    llm = get_llm("generate_question_node", state["llm_config"])
    structured_llm = llm.with_structured_output(GeneratedQuestionSchema)

    qa_summary = summarize_qa_history(state["qa_history"])

    prompt = GENERATE_QUESTION_PROMPT.format(
        analyser_output=state["analyser_output"],
        qa_history=qa_summary,
        unanswered_questions=unanswered,
        retrieved_chunks=relevant_chunks,
    )
    result = structured_llm.invoke(prompt)
    result_dict = result.model_dump()

    # 5. Handle terminate signal
    if result_dict.get("terminate"):
        publisher.emit("node_complete", {
            "node": "generate_question_node",
            "terminated": True,
            "reason": result_dict.get("reason", "LLM signalled no high-value questions"),
        })
        return {"current_question": None}

    # 6. Construct the QAExchange
    current_question = QAExchange(
        question_id=result_dict["question_id"],
        question=result_dict["question"],
        rationale=result_dict["rationale"],
        options=result_dict["options"],
        answer=None,
        selected_option_index=None,
        status="answered",   # placeholder — overwritten on resume
        timestamp=now_iso(),
        triggered_changes=[],
    )

    publisher.emit("question_ready", {
        "node": "generate_question_node",
        "question": current_question,
        "allow_free_text": True,
        "allow_skip": True,
    })
    publisher.emit("node_complete", {"node": "generate_question_node"})

    return {
        "current_question": current_question,
        "questions_asked_count": state["questions_asked_count"] + 1,
    }
```

**Streaming events.**
- `node_start`
- `question_ready` — frontend renders the question card
- `node_complete`

**Error handling.**
- LLM picks a `question_id` that doesn't exist in `analyser_output.open_questions`: regenerate with explicit "must use one of these IDs: [...]" prompt.
- LLM returns fewer than 2 options: regenerate.
- Persistent failure: terminate the loop (set `current_question = None`) so we don't get stuck.

---

### 10.9 await_answer_node (discovery subgraph, interrupt placeholder)

**Purpose.** Pure no-op. The graph is configured with `interrupt_before=["await_answer_node"]`, so it pauses *before* this node ever runs. When the user submits an answer via the API, `Command(resume=...)` injects the answer into `current_question`. This node then runs trivially (state is already updated) and forwards to `process_answer_node`.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | (none) | |
| Writes | (none) | |

**Pseudocode.**

```python
def await_answer_node(state: DiscoveryState, config) -> dict:
    """Placeholder — graph interrupts BEFORE this node.
    Resume handler updates current_question; this node forwards.
    """
    return {}
```

**Streaming events.** None directly. The `interrupt` event is emitted by LangGraph itself when the pause occurs.

**Error handling.** N/A — there's nothing to fail.

---

### 10.10 process_answer_node (discovery subgraph, LLM node)

**Purpose.** Take the just-answered question, ask the LLM to generate JSON patches against `analyser_output`, apply those patches deterministically, and append the QAExchange to `qa_history`. Also handle skip / N/A actions appropriately.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `current_question` (now with answer), `analyser_output`, `working_chunk_ids` | |
| Writes | `analyser_output` | Mutated by patches |
| Writes | `qa_history` (append) | Adds the completed exchange |
| Writes | `current_question: None` | Cleared |
| Writes | `delta_changes` (append) | One per patch |

**Pseudocode.**

```python
def process_answer_node(state: DiscoveryState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "process_answer_node"})

    qa = state["current_question"]
    if qa is None:
        # Defensive: shouldn't happen if interrupt was resumed properly
        return {}

    new_deltas = []
    new_analyser = deepcopy(state["analyser_output"])
    triggered_changes = []

    # ── Branch by user action ──

    if qa["status"] == "answered":
        # Ask LLM what fields to patch
        rag_retriever = RawRagRetriever(
            project_id=state["project_id"],
            version=state["version"],
        )
        grounding = rag_retriever.retrieve(query=qa["question"], k=3)

        llm = get_llm("process_answer_node", state["llm_config"])
        structured_llm = llm.with_structured_output(JsonPatchListSchema)

        prompt = PROCESS_ANSWER_PROMPT.format(
            qa=qa,
            analyser_output=new_analyser,
            grounding=grounding,
        )
        patch_result = structured_llm.invoke(prompt)
        patches = patch_result.model_dump()["patches"]

        # Apply patches deterministically — NEVER let the LLM rewrite the doc
        for patch in patches:
            try:
                old_value = jsonpointer.resolve(
                    new_analyser, patch["path"], default=None
                )
                new_analyser = jsonpatch.JsonPatch([{
                    "op": patch["op"],
                    "path": patch["path"],
                    "value": patch.get("value"),
                }]).apply(new_analyser)

                delta = DeltaChange(
                    change_id=str(uuid4()),
                    source="qa",
                    source_ref=qa["question_id"],
                    field_path=patch["path"],
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(patch.get("value", "")),
                    timestamp=now_iso(),
                )
                new_deltas.append(delta)
                triggered_changes.append({
                    "path": patch["path"],
                    "reasoning": patch.get("reasoning", ""),
                })
                publisher.emit("delta_change", delta)
            except Exception as e:
                log.warning(f"Skipped patch {patch}: {e}")
                continue

    elif qa["status"] == "deferred":
        # Skip — keep question in open_questions, tag as ask_client
        for q in new_analyser["open_questions"]:
            if q["question_id"] == qa["question_id"]:
                q["priority"] = "low"
                q.setdefault("blocked_decisions", []).append("ask_client_later")
                break

    elif qa["status"] == "na":
        # Remove from open_questions entirely
        new_analyser["open_questions"] = [
            q for q in new_analyser["open_questions"]
            if q["question_id"] != qa["question_id"]
        ]

    elif qa["status"] == "unknown":
        # Stays in open_questions; analytics will count it as unknown
        for q in new_analyser["open_questions"]:
            if q["question_id"] == qa["question_id"]:
                q.setdefault("blocked_decisions", []).append("unknown_for_analytics")
                break

    # Finalize the QAExchange and append to history
    qa["triggered_changes"] = triggered_changes
    completed_qa = qa

    publisher.emit("node_complete", {
        "node": "process_answer_node",
        "patches_applied": len(new_deltas),
        "status": qa["status"],
    })

    return {
        "analyser_output": new_analyser,
        "qa_history": [completed_qa],          # appended via reducer
        "current_question": None,              # clear
        "delta_changes": new_deltas,           # appended via reducer
    }
```

**Streaming events.**
- `node_start`
- `delta_change` per patch applied
- `node_complete` with patch count and final status

**Error handling.**
- Per-patch try/except: a bad patch path doesn't kill the whole answer processing.
- LLM returns no patches when an answer should clearly trigger one: log warning but don't fail — sometimes the answer just confirms existing analysis.
- Patch path doesn't exist: skip and log. Common when LLM hallucinates a field.

---

### 10.11 finalize_doc_node (discovery subgraph, deterministic)

**Purpose.** Render `analyser_output` + `qa_history` into a clean markdown document via Jinja2 template. NO LLM. Deterministic, reproducible, fast.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `analyser_output`, `qa_history` | |
| Writes | `final_doc_markdown: str` | |

**Pseudocode.**

```python
def finalize_doc_node(state: DiscoveryState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "finalize_doc_node"})

    template = jinja_env.get_template("final_analysis.md.j2")
    markdown = template.render(
        executive_summary=state["analyser_output"]["executive_summary"],
        project_overview=state["analyser_output"]["project_overview"],
        functional_requirements=group_by_moscow(
            state["analyser_output"]["functional_requirements"]
        ),
        risks=sorted(
            state["analyser_output"]["risks"],
            key=lambda r: SEVERITY_ORDER[r["severity"]],
        ),
        recommended_team=state["analyser_output"]["recommended_team"],
        open_questions=state["analyser_output"]["open_questions"],
        qa_history=[qa for qa in state["qa_history"] if qa["status"] == "answered"],
        completeness_score=state["analyser_output"]["completeness_score"],
        assumptions_made=state["analyser_output"]["assumptions_made"],
        generated_at=now_iso(),
    )

    publisher.emit("final_doc_ready", {
        "node": "finalize_doc_node",
        "markdown": markdown,
    })
    publisher.emit("node_complete", {"node": "finalize_doc_node"})

    return {"final_doc_markdown": markdown}
```

**Streaming events.** `node_start`, `final_doc_ready` with full markdown, `node_complete`.

**Error handling.** Template rendering errors mean a developer typo. Hard fail, log loudly.

---

### 10.12 route_review_2_node (parent, deterministic router)

**Purpose.** This is the node that fires *after* `human_review_2` interrupt resumes. Its only job is to be the resume target — the actual routing happens in the conditional edge that follows it. It exists as a node (rather than just an edge) so the interrupt has a clean attachment point.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `review_2_status` | |
| Writes | (nothing — just a pass-through) | |

**Pseudocode.**

```python
def route_review_2_node(state: GraphState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "route_review_2_node"})
    publisher.emit("node_complete", {
        "node": "route_review_2_node",
        "review_2_status": state["review_2_status"],
    })
    return {}
```

The conditional edge (defined in the parent graph compose) routes based on `review_2_status`:
- `approved` → `approved_rag_index_node`
- `edits_made` → `apply_review_2_edits_node`
- `more_questions` → `discovery_subgraph` (loop back)

**Streaming events.** `node_start`, `node_complete`.

**Error handling.** N/A — pure router.

---

### 10.13 apply_review_2_edits_node (parent, deterministic)

**Purpose.** Apply user edits to either `analyser_output` (if structured edits) or `final_doc_markdown` (if direct markdown edits), then loop back to `route_review_2_node` for re-review.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `user_edits_payload`, `analyser_output`, `final_doc_markdown` | |
| Writes | `analyser_output` and/or `final_doc_markdown` | |
| Writes | `final_doc_markdown` | Re-rendered if structured edits were applied |
| Writes | `delta_changes` (append) | |
| Writes | `user_edits_payload: None` | Cleared |

**Pseudocode.**

```python
def apply_review_2_edits_node(state: GraphState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "apply_review_2_edits_node"})

    payload = state["user_edits_payload"] or {}
    edit_mode = payload.get("mode")   # "structured" or "markdown"

    new_analyser = state["analyser_output"]
    new_markdown = state["final_doc_markdown"]
    new_deltas = []

    if edit_mode == "structured":
        # Apply JSON patches to analyser_output, then re-render markdown
        new_analyser = deepcopy(state["analyser_output"])
        for patch in payload["patches"]:
            old_value = jsonpointer.resolve(new_analyser, patch["path"], default=None)
            new_analyser = jsonpatch.JsonPatch([patch]).apply(new_analyser)
            new_deltas.append(DeltaChange(
                change_id=str(uuid4()),
                source="user_edit",
                source_ref="review_2_structured",
                field_path=patch["path"],
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(patch.get("value", "")),
                timestamp=now_iso(),
            ))
        # Re-render markdown to reflect new analyser_output
        # (small: just call the same Jinja template as finalize_doc_node)
        new_markdown = render_final_doc_markdown(new_analyser, state["qa_history"])

    elif edit_mode == "markdown":
        # User edited the markdown directly. Trust them; don't re-derive analyser_output.
        new_markdown = payload["new_markdown"]
        new_deltas.append(DeltaChange(
            change_id=str(uuid4()),
            source="user_edit",
            source_ref="review_2_markdown",
            field_path="final_doc_markdown",
            old_value="(replaced)",
            new_value="(replaced)",
            timestamp=now_iso(),
        ))

    publisher.emit("node_complete", {
        "node": "apply_review_2_edits_node",
        "edit_mode": edit_mode,
    })

    return {
        "analyser_output": new_analyser,
        "final_doc_markdown": new_markdown,
        "delta_changes": new_deltas,
        "user_edits_payload": None,
        "review_2_status": "pending",   # reset for re-review
    }
```

**Streaming events.** `node_start`, `node_complete`.

**Error handling.** Same per-patch try/except as `apply_review_1_edits_node`.

---

### 10.14 approved_rag_index_node (parent, tool node)

**Purpose.** After Stage 2 is approved, section-chunk the final `analyser_output`, embed each chunk, and write to permanent `requirement_nodes` table. Versioned — old versions never deleted.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `analyser_output`, `final_doc_markdown`, `qa_history`, `project_id`, `version` | |
| Side effect | Inserts rows into `requirement_nodes` | |
| Side effect | Inserts into `stage_outputs` with status="approved" | |

**Pseudocode.**

```python
def approved_rag_index_node(state: GraphState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "approved_rag_index_node"})

    chunks = []

    # 1. Executive summary — 1 chunk
    chunks.append(make_chunk(
        text=state["analyser_output"]["executive_summary"],
        section_type="exec_summary",
        metadata={"stage_origin": "stage_1"},
    ))

    # 2. Project overview sub-sections — 1 chunk each
    for key in ("objective", "scope", "out_of_scope"):
        if state["analyser_output"]["project_overview"].get(key):
            chunks.append(make_chunk(
                text=state["analyser_output"]["project_overview"][key],
                section_type=f"project_overview_{key}",
                metadata={"stage_origin": "stage_1"},
            ))

    # 3. Functional requirements — 1 chunk PER requirement
    for req in state["analyser_output"]["functional_requirements"]:
        chunks.append(make_chunk(
            text=format_requirement_for_embedding(req),
            section_type=f"{req['moscow']}_req",
            metadata={
                "moscow_priority": req["moscow"],
                "req_id": req["req_id"],
                "source": req["source"],
                "stage_origin": "stage_1" if req["source"] == "document" else "stage_2",
            },
        ))

    # 4. Risks — 1 chunk per risk
    for risk in state["analyser_output"]["risks"]:
        chunks.append(make_chunk(
            text=format_risk_for_embedding(risk),
            section_type="risk",
            metadata={
                "severity": risk["severity"],
                "category": risk["category"],
                "risk_id": risk["risk_id"],
                "stage_origin": "stage_1",
            },
        ))

    # 5. Recommended team — 1 chunk
    chunks.append(make_chunk(
        text=format_team_for_embedding(state["analyser_output"]["recommended_team"]),
        section_type="recommended_team",
        metadata={"stage_origin": "stage_1"},
    ))

    # 6. Open questions still unresolved — 1 chunk per question
    for q in state["analyser_output"]["open_questions"]:
        chunks.append(make_chunk(
            text=q["question"],
            section_type="open_question",
            metadata={
                "question_id": q["question_id"],
                "priority": q["priority"],
                "stage_origin": "stage_1",
            },
        ))

    # 7. QA resolutions — 1 chunk per ANSWERED Q&A
    for qa in state["qa_history"]:
        if qa["status"] != "answered":
            continue
        chunks.append(make_chunk(
            text=format_qa_for_embedding(qa),
            section_type="qa_resolution",
            metadata={
                "source_question_id": qa["question_id"],
                "stage_origin": "stage_2",
            },
        ))

    # 8. Batch embed
    BATCH_SIZE = 100
    embeddings = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_embeddings = embedding_client.embed_batch([c["text"] for c in batch])
        embeddings.extend(batch_embeddings)
        publisher.emit("progress", {
            "node": "approved_rag_index_node",
            "completed": i + len(batch),
            "total": len(chunks),
        })

    # 9. Bulk insert with project_id + version metadata
    rows = []
    for chunk, emb in zip(chunks, embeddings):
        rows.append({
            "node_id": uuid4(),
            "project_id": state["project_id"],
            "version": state["version"],
            "section_type": chunk["section_type"],
            "text": chunk["text"],
            "metadata": chunk["metadata"],
            "embedding": emb,
        })
    bulk_insert("requirement_nodes", rows)

    # 10. Persist final stage_output with approved status
    insert_stage_output(
        project_id=state["project_id"],
        version=state["version"],
        stage="discovery",
        output_json={
            "analyser_output": state["analyser_output"],
            "qa_history": state["qa_history"],
            "delta_changes": state["delta_changes"],
        },
        approved_at=now_iso(),
    )

    publisher.emit("node_complete", {
        "node": "approved_rag_index_node",
        "chunks_indexed": len(chunks),
    })

    return {}
```

**Streaming events.** `node_start`, `progress` per batch, `node_complete`.

**Error handling.** Same as `raw_rag_index_node` — retry per batch, log persistent failures.

---

### 10.15 artifact_export_node (parent, tool node)

**Purpose.** Render the final markdown to PDF (via WeasyPrint) and DOCX (via python-docx). Upload both to MinIO `bra-exports` bucket. Store the keys in state.

**Contract.**

| Direction | Key | Notes |
|---|---|---|
| Reads | `final_doc_markdown`, `project_id`, `version` | |
| Writes | `final_doc_pdf_s3_key`, `final_doc_docx_s3_key` | |
| Side effect | Uploads to MinIO `bra-exports` | |

**Pseudocode.**

```python
def artifact_export_node(state: GraphState, config) -> dict:
    publisher = config["configurable"]["event_publisher"]
    publisher.emit("node_start", {"node": "artifact_export_node"})

    project_id = state["project_id"]
    version = state["version"]

    # 1. Render PDF via WeasyPrint
    publisher.emit("tool_call", {
        "node": "artifact_export_node",
        "tool": "weasyprint",
    })
    html = markdown_to_html(state["final_doc_markdown"])
    pdf_bytes = weasyprint.HTML(string=html).write_pdf()
    pdf_key = f"{project_id}/v{version}/analysis.pdf"
    upload_to_minio(
        bucket=settings.S3_BUCKET_EXPORTS,
        key=pdf_key,
        body=pdf_bytes,
        content_type="application/pdf",
    )

    # 2. Render DOCX via python-docx
    publisher.emit("tool_call", {
        "node": "artifact_export_node",
        "tool": "python-docx",
    })
    docx_bytes = render_docx_from_markdown(state["final_doc_markdown"])
    docx_key = f"{project_id}/v{version}/analysis.docx"
    upload_to_minio(
        bucket=settings.S3_BUCKET_EXPORTS,
        key=docx_key,
        body=docx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    # 3. Build pre-signed download URLs (24h expiry)
    pdf_url = generate_presigned_url(settings.S3_BUCKET_EXPORTS, pdf_key, expiry=86400)
    docx_url = generate_presigned_url(settings.S3_BUCKET_EXPORTS, docx_key, expiry=86400)

    publisher.emit("artifact_ready", {
        "node": "artifact_export_node",
        "pdf_url": pdf_url,
        "docx_url": docx_url,
    })
    publisher.emit("node_complete", {"node": "artifact_export_node"})

    return {
        "final_doc_pdf_s3_key": pdf_key,
        "final_doc_docx_s3_key": docx_key,
    }
```

**Streaming events.**
- `node_start`
- `tool_call` per renderer
- `artifact_ready` with pre-signed URLs
- `node_complete`

**Error handling.**
- WeasyPrint failure (rare): log, attempt fallback to a simpler renderer (markdown → HTML → headless-Chromium PDF), or fail loudly.
- DOCX render failure: skip DOCX but still return PDF — better to give the user something.
- MinIO upload failure: retry once, then fail.

---

## 11. RAG Strategy — Dual Index

Two indices, two purposes, two chunking strategies.

### 11.1 Index A — working_chunks (pre-approval, in-flight retrieval)

**Purpose:** Let `enrich_node`, `analyse_node`, `prioritize_questions_node`, and `process_answer_node` query the raw uploaded doc semantically while reasoning. For 2-3 page docs barely needed; future-proofs for 50MB uploads.

**Schema:**
```sql
CREATE TABLE working_chunks (
    chunk_id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    version INT NOT NULL,
    text TEXT NOT NULL,
    metadata JSONB NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    tsv tsvector GENERATED ALWAYS AS
        (to_tsvector('english', text)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX ON working_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON working_chunks USING gin (tsv);
CREATE INDEX ON working_chunks (project_id, version);
CREATE INDEX ON working_chunks USING gin (metadata);
```

**Chunking strategy:**
- Recursive character splitter, **1000 chars / 200 overlap**, with semantic boundary preference: `\n\n` > `\n` > `. ` > ` `
- **Tables stay intact.** Even if > 1000 chars, one chunk per table. Don't split rows.
- **Images get described** by vision LLM. Description becomes chunk text; original image S3 key in metadata. Handles BRD's "images, tables, diagrams" requirement.
- **Headings carried in metadata.** Extract from DOCX styles, PDF font sizes. Massive retrieval-quality boost.

**Per-chunk metadata:**
```python
{
    "file_name": str,
    "page": int | None,
    "section_heading": str | None,
    "content_type": "text" | "table" | "image_description",
    "raw_image_ref": str | None,
}
```

**Retrieval — Hybrid (vector + tsvector + RRF):**

```python
def raw_rag_retrieve(query: str, project_id: str, version: int, k: int = 5):
    # 1. Vector search via pgvector cosine similarity
    # 2. Keyword search via tsvector
    # 3. Combine with Reciprocal Rank Fusion
    # 4. Filter: WHERE project_id = ? AND version = ?
    # Return top-k chunks with metadata
```

Pure vector misses exact terms ("section 4.2.1"). Pure keyword misses paraphrases ("response time" vs "latency SLA"). Hybrid catches both. RRF formula: `score(d) = Σ 1/(k + rank_i(d))` across both ranking sources, k=60 conventional.

**TTL policy:** Working chunks expire 30 days after last project activity. Nightly cleanup job:
```sql
DELETE FROM working_chunks WHERE expires_at < NOW();
```

### 11.2 Index B — requirement_nodes (post-approval, permanent)

**Purpose:** Canonical retrieval index. Stage 3, Stage 4, and any future feature (cross-project search, duplicate detection, change-impact assessment) queries this.

**Schema:**
```sql
CREATE TABLE requirement_nodes (
    node_id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    version INT NOT NULL,
    section_type TEXT NOT NULL,
    text TEXT NOT NULL,
    metadata JSONB NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
    -- NO expires_at — these are permanent
);
CREATE INDEX ON requirement_nodes USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON requirement_nodes (project_id, version);
CREATE INDEX ON requirement_nodes (section_type);
CREATE INDEX ON requirement_nodes USING gin (metadata);
```

**Chunking strategy — section-based, NOT character-based:**

| Section type | Chunking rule |
|---|---|
| `exec_summary` | 1 chunk |
| `project_overview` | 1 chunk per sub-section (objective, scope, out_of_scope) |
| `must_have_req` | **1 chunk per requirement** |
| `should_have_req` | 1 chunk per requirement |
| `good_to_have_req` | 1 chunk per requirement |
| `risk` | 1 chunk per risk |
| `recommended_team` | 1 chunk |
| `open_question` | 1 chunk per unresolved question |
| `qa_resolution` | 1 chunk per resolved Q&A (text = question + answer + what changed) |

**Why section-based:** Stage 3 (Architecture) and Stage 4 (Sprint) will query things like "what are all the must-have requirements?" Section chunks return complete logical units. Character chunks would return half-requirements.

**The `qa_resolution` chunks are gold.** They preserve the *reasoning* behind decisions. When Stage 3 asks "why is this a must-have?" it can retrieve the QA exchange that elevated it.

**Per-chunk metadata:**
```python
{
    "section_type": str,
    "moscow_priority": str | None,        # for requirement chunks
    "severity": str | None,                # for risk chunks
    "source_question_id": str | None,      # if produced/modified by QA
    "stage_origin": "stage_1" | "stage_2",
    "created_at": str,
}
```

**Retrieval — Pure vector + metadata SQL filter:**
No need for hybrid here because section chunks are semantically clean and metadata is rich. Example query:

```sql
SELECT node_id, text, metadata
FROM requirement_nodes
WHERE project_id = $1
  AND version = $2
  AND metadata->>'moscow_priority' = 'must_have'
ORDER BY embedding <=> $3 LIMIT 5;
```

**Versioning policy:** When v2 is approved, **insert new rows with `version=2`** alongside existing v1 rows. Nothing is deleted. Downstream queries filter by current version. Free audit history and diff capability.

### 11.3 Which index each node queries

| Node | Index queried | Why |
|---|---|---|
| `enrich_node` | working_chunks | Needs raw doc context to know what to fill in |
| `analyse_node` | working_chunks | Grounds the analysis in actual doc content |
| `prioritize_questions_node` | working_chunks | Checks if doc already implicitly answers a question |
| `process_answer_node` | working_chunks | Validates answer against doc context |
| Stage 3+ (later) | requirement_nodes | Builds on approved analysis, not raw doc |

---

## 12. Question Generation Strategy

### 12.1 The prompt

```
SYSTEM:
You are a senior business analyst conducting a discovery session with a
product manager. You have:

1. CURRENT ANALYSIS STATE:
{analyser_output_json}

2. QUESTIONS ALREADY ASKED THIS SESSION:
{qa_history_summary}

3. RELEVANT EXCERPTS FROM THE UPLOADED DOCUMENT:
{retrieved_chunks}

YOUR TASK:
Generate the SINGLE most impactful next question, OR signal that no
further high-value questions remain.

DECISION RULES:
- Pick the question whose answer would unblock the MOST downstream
  decisions (architecture, scope, MVP boundary, team size, risks).
- Do not ask anything already definitively answered in the document or
  in prior QA history.
- Do not ask trivia. Every question must change the analysis if answered.
- Provide 2-4 concrete answer options that span the realistic decision
  space. Options must be mutually distinct and collectively cover the
  common cases.
- Include a `rationale` explaining what this question unblocks.
- If you have no high-value questions left, return:
  {"terminate": true, "reason": "..."}

OUTPUT (strict JSON):
{
  "terminate": false,
  "question_id": "q_<short uuid>",
  "question": "...",
  "rationale": "...",
  "options": ["...", "..."],
  "priority": "high" | "medium" | "low",
  "blocked_decisions": ["which downstream decisions this unblocks"]
}
```

### 12.2 Question card payload (backend → frontend, via WebSocket)

```json
{
  "type": "question_ready",
  "question_id": "q_abc123",
  "question": "What's the expected concurrent user load at launch?",
  "rationale": "This determines whether we recommend a single-region deployment or multi-region from day one — affects Stage 3 architecture and Stage 4 sprint scope.",
  "options": [
    "Under 1,000 users",
    "1,000 – 10,000 users",
    "10,000 – 100,000 users",
    "Over 100,000 users"
  ],
  "allow_free_text": true,
  "allow_skip": true,
  "priority": "high"
}
```

### 12.3 Answer payload (frontend → backend, REST)

`POST /api/projects/{project_id}/discovery/answer`

```json
{
  "question_id": "q_abc123",
  "action": "answer" | "skip" | "not_applicable",
  "selected_option_index": 1,
  "free_text": null
}
```

### 12.4 Status mapping

| `action` | Resulting `status` | Behavior |
|---|---|---|
| `answer` (option selected) | `answered` | Use option text as answer |
| `answer` (free text provided) | `answered` | Use free text as answer |
| `skip` | `deferred` | Add to `open_questions` tagged `priority=ask_client` for future client session |
| `not_applicable` | `na` | Remove from `open_questions` entirely |
| (skipped without info, recorded for analytics) | `unknown` | Counts as "unknown parameter" in completeness metrics |

### 12.5 Termination conditions

The discovery loop exits when ANY of:
- LLM returns `{"terminate": true}` — no high-value questions left
- `questions_asked_count >= 10` (hard cap)
- All `analyser_output.open_questions` are resolved or in `qa_history`
- User clicks "I'm done with questions" — sets `discovery_terminated = True`

---

## 13. Per-Agent LLM Configuration

The BRD requires runtime per-agent LLM switching. Implementation:

```python
# bra_agents/shared/llm_factory.py

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

def get_llm(agent_id: str, llm_config: dict[str, dict]):
    """
    agent_id is the node name. llm_config comes from GraphState
    (loaded from llm_configs table at graph entry).
    """
    cfg = llm_config.get(agent_id) or llm_config["default"]
    provider = cfg["provider"]

    if provider == "openai":
        return ChatOpenAI(
            model=cfg["model_name"],
            temperature=cfg.get("temperature", 0.2),
            max_tokens=cfg.get("max_tokens", 4096),
            streaming=True,
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=cfg["model_name"],
            temperature=cfg.get("temperature", 0.2),
            max_tokens=cfg.get("max_tokens", 4096),
            streaming=True,
        )
    raise ValueError(f"Unknown provider: {provider}")
```

**Usage inside any node:**
```python
def analyse_node(state: AnalyserState) -> dict:
    llm = get_llm("analyse_node", state["llm_config"])
    structured_llm = llm.with_structured_output(AnalyserResultSchema)
    result = structured_llm.invoke(...)
    return {"analyser_output": result.model_dump()}
```

**Agent IDs (= node names):**
- `score_node`
- `enrich_node`
- `analyse_node`
- `prioritize_questions_node`
- `generate_question_node`
- `process_answer_node`
- `default` (fallback)

The UI's per-agent config panel just lists these keys from the `llm_configs` table. Updates via `PUT /api/settings/llm-config/{agent_id}`.

---

## 14. Streaming Layer

### 14.1 Pipeline

```
LangGraph node execution
         │
         │  app.astream_events(state, config, version="v2")
         ▼
Event stream from LangGraph
         │
         │  transform_to_ws_event(event)
         ▼
Redis pub/sub channel: "project:{project_id}:stream"
         │
         │  WebSocket subscriber
         ▼
Frontend WebSocket receiver
         │
         ▼
Three UI affordances:
  • Stepper (driven by node_start/complete)
  • Live document panel (driven by token)
  • Activity log (driven by tool_call)
```

### 14.2 Backend runner

```python
# bra_agents/runner/graph_runner.py

async def run_graph_streaming(project_id: str, initial_state: GraphState):
    config = {"configurable": {"thread_id": project_id}}

    async for event in app.astream_events(
        initial_state, config, version="v2"
    ):
        ws_event = transform_to_ws_event(event)
        if ws_event is None:
            continue
        await publish_to_redis_channel(
            f"project:{project_id}:stream",
            ws_event,
        )
```

### 14.3 Event taxonomy

| LangGraph internal event | Your WS event |
|---|---|
| `on_chain_start` (node) | `node_start` |
| `on_chain_end` (node) | `node_complete` |
| `on_chat_model_stream` | `token` |
| `on_tool_start` | `tool_call` |
| `on_tool_end` | `tool_complete` |
| (custom — emitted from inside nodes) | `score_ready`, `analysis_ready`, `question_ready`, `delta_change`, `final_doc_ready`, `artifact_ready` |
| LangGraph interrupt | `interrupt` |
| Exception | `error` |

### 14.4 WebSocket event schema

| Event | Payload |
|---|---|
| `node_start` | `{node, timestamp}` |
| `node_complete` | `{node, duration_ms}` |
| `token` | `{node, token}` |
| `tool_call` | `{node, tool, input_summary}` |
| `tool_complete` | `{node, tool, duration_ms}` |
| `score_ready` | full `ScoreBreakdown` |
| `analysis_ready` | full `AnalyserResult` |
| `question_ready` | full `QAExchange` (see §12.2) |
| `delta_change` | full `DeltaChange` |
| `final_doc_ready` | `{markdown}` |
| `artifact_ready` | `{pdf_url, docx_url}` |
| `interrupt` | `{node, reason}` |
| `error` | `{node, error_type, message, retriable}` |

### 14.5 Custom events from inside nodes

```python
def analyse_node(state, config):
    publisher = config["configurable"]["event_publisher"]
    # ... do work ...
    publisher.emit("analysis_ready", {"analyser_output": result})
    return {"analyser_output": result}
```

The publisher is injected through node config at graph invocation time.

### 14.6 Subgraph event namespacing

`astream_events(version="v2")` automatically tags events with the node path. Events from inside the Analyser subgraph come tagged like `parent.analyser_subgraph.score_node`. Use this hierarchy in WS payload so frontend stepper shows the right level of detail.

---

## 15. Resume Mechanics (Interrupts)

When the graph hits an interrupt, the API resumes via `Command(resume=...)`.

### 15.1 Discovery answer resume

```python
# bra_agents/api/routes/discovery.py

@router.post("/projects/{project_id}/discovery/answer")
async def submit_answer(project_id: str, body: AnswerPayload):
    # 1. Build the QAExchange update
    answered_question = build_answered_question(body, current_question)

    # 2. Resume with Command
    config = {"configurable": {"thread_id": project_id}}
    async for event in app.astream_events(
        Command(resume={"current_question": answered_question}),
        config,
        version="v2",
    ):
        await publish_event(project_id, event)

    return {"status": "answered"}
```

### 15.2 Stage approval resume

```python
# bra_agents/api/routes/reviews.py

@router.post("/projects/{project_id}/approve/{stage}")
async def approve_stage(project_id: str, stage: str, body: ApprovePayload):
    if stage == "stage_1":
        update = {
            "review_1_status": body.action,    # "approved" or "edits_made"
            "user_edits_payload": body.edits,
        }
    elif stage == "stage_2":
        update = {
            "review_2_status": body.action,    # approved/edits_made/more_questions
            "user_edits_payload": body.edits,
        }

    config = {"configurable": {"thread_id": project_id}}
    async for event in app.astream_events(
        Command(resume=update), config, version="v2",
    ):
        await publish_event(project_id, event)
    return {"status": "ok"}
```

### 15.3 Stale tab guard

If a user opens a stale browser tab and tries to resume an already-resumed thread, you get a state conflict. Guard pattern:

```python
state = await app.aget_state(config)
if state.next != ("expected_interrupt_node",):
    raise HTTPException(409, "Thread is not paused at this interrupt")
```

### 15.4 Subgraph interrupt routing

For Discovery's `await_answer_node` interrupt (inside the subgraph), the parent graph also pauses. The API resumes with `Command(resume=...)` on the parent's `thread_id` — LangGraph's checkpointer routes the update to the right place inside the subgraph automatically. No explicit "resume into subgraph" is needed.

---

## 16. Database Schema

### 16.1 Core tables (BRD-aligned, no-auth phase)

> **No-auth phase:** No `users` table. No `created_by` / `approved_by` foreign keys. No `api_key_ref` (LLM API keys come from `.env`). When auth is added later, a clean migration will introduce `users` and add foreign-key columns to these tables.

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    current_stage TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE project_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    version_number INT NOT NULL,
    snapshot_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (project_id, version_number)
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    parsed_text_s3_key TEXT,
    score JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE stage_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    version INT NOT NULL,
    stage TEXT NOT NULL,                  -- 'analyse', 'discovery'
    output_json JSONB NOT NULL,
    approved_at TIMESTAMPTZ,
    edits_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE discovery_qa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    version INT NOT NULL,
    question_id TEXT NOT NULL,
    question TEXT NOT NULL,
    rationale TEXT,
    options JSONB NOT NULL,
    answer TEXT,
    selected_option_index INT,
    status TEXT NOT NULL,                 -- answered/deferred/na/unknown
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE change_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id),
    version INT NOT NULL,
    source_node TEXT NOT NULL,
    description TEXT NOT NULL,
    field_path TEXT,
    old_value TEXT,
    new_value TEXT,
    triggered_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE llm_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id TEXT NOT NULL UNIQUE,        -- node name
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    temperature REAL DEFAULT 0.2,
    max_tokens INT DEFAULT 4096,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
-- Note: API keys are NOT stored here in the no-auth phase.
-- They come from .env (OPENAI_API_KEY, ANTHROPIC_API_KEY).
-- When auth + secrets-manager are added later, add an api_key_ref column.
```

### 16.2 RAG tables

See §11.1 (`working_chunks`) and §11.2 (`requirement_nodes`).

### 16.3 LangGraph checkpointer tables

Managed automatically by `langgraph.checkpoint.postgres.PostgresSaver`. Tables: `checkpoints`, `checkpoint_writes`, `checkpoint_blobs`. Run `PostgresSaver.from_conn_string(...).setup()` once at install.

### 16.4 Checkpointer growth policy

Every node transition writes a checkpoint. For a project with 10 questions answered, that's ~30+ checkpoints. After graph reaches `END`:
- State is preserved in `stage_outputs` and `requirement_nodes`
- Checkpoints can be archived/pruned
- Recommend a nightly job: prune checkpoints for threads in terminal state older than 30 days

---

## 17. API Endpoints

> **No-auth phase:** All endpoints below are open. No `Authorization` header. No CORS restriction (set `allow_origins=["*"]` for local dev). When auth is added, wrap the entire `/api` router with a single `Depends(get_current_user)` and add `user_id` filtering at the query layer — no per-endpoint changes needed.

### 17.1 REST endpoints (your scope)

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/projects` | Create new project session |
| `GET` | `/api/projects/{id}` | Get project with all stage outputs |
| `POST` | `/api/projects/{id}/documents` | Upload documents (multipart/form-data) |
| `POST` | `/api/projects/{id}/analyse` | Trigger graph from start (Stage 1+2) |
| `POST` | `/api/projects/{id}/approve/{stage}` | Submit approval (Stage 1 or 2) with optional edits |
| `GET` | `/api/projects/{id}/discovery` | Get current Q&A state |
| `POST` | `/api/projects/{id}/discovery/answer` | Submit answer to current question |
| `POST` | `/api/projects/{id}/discovery/end` | End discovery early (sets `discovery_terminated`) |
| `POST` | `/api/projects/{id}/finalize` | Finalize and create version snapshot (handled by graph automatically post-approval) |
| `GET` | `/api/projects/{id}/versions` | List all versions |
| `POST` | `/api/projects/{id}/export` | Get download URL for PDF/DOCX |
| `GET` | `/api/settings/llm-config` | Get LLM config per agent |
| `PUT` | `/api/settings/llm-config/{agent_id}` | Update LLM model for a specific agent |

### 17.2 WebSocket endpoint

`WS /ws/projects/{project_id}/stream`

- Real-time streaming of agent output tokens, tool calls, node events, questions
- Event format: `{ type: string, node: string, payload: object, timestamp: string }`
- Subscriber pattern: connect → subscribe to `project:{project_id}:stream` Redis channel → forward all messages to WS client

---

## 18. Implementation Gotchas

### 18.1 Subgraph composition

1. **Don't compile subgraphs with their own checkpointer.** Only the parent has a checkpointer. Subgraphs inherit. Compiling with `compile(checkpointer=...)` causes silent state corruption.

2. **State key overlaps must be exact.** If parent has `qa_history: list[QAExchange]` but subgraph declares `qa_history: list[Question]` (slightly different type), TypedDict won't catch it but runtime serialization will fail.

3. **`Annotated[list, add]` reducers must match across parent and subgraph.** If parent says `Annotated[list, add]` and subgraph says plain `list`, the subgraph silently overwrites the parent's accumulated list.

### 18.2 Streaming

4. **Subgraph events are nested in the event hierarchy.** When iterating `astream_events`, `event["metadata"]["langgraph_node"]` includes the subgraph name. Use this to namespace WS events.

5. **Token streaming through async generators across WebSocket connections is fiddly.** Use Redis pub/sub or `asyncio.Queue` between graph runner and WS handler. Don't try to write tokens directly from inside a node.

### 18.3 RAG and embeddings

6. **Embedding cost batching.** Don't embed chunks one at a time. OpenAI's embedding endpoint accepts hundreds of inputs per call. Batch in groups of 50-100.

7. **Vision LLM cost for image-in-doc.** Each image = one LLM call. Cache by image hash so re-runs don't re-pay.

8. **Vectors do NOT live in graph state.** Only chunk IDs do. Otherwise checkpoints bloat to MBs.

### 18.4 Process answer node

9. **JSON patches in `process_answer_node` must be applied in code, not by the LLM.** The LLM returns patches; deterministic code applies them. Otherwise the LLM rewrites the whole AnalyserResult and you lose the audit trail.

10. **Use the `jsonpatch` library** for applying patches — it's RFC 6902 compliant and handles edge cases.

### 18.5 Web search

11. **Web search inside `enrich_node` should be rate-limited and capped.** Cap at 5 searches per enrich call. Otherwise the LLM searches for everything and pollutes assumptions list.

### 18.6 Interrupts

12. **Interrupt resume payloads must match state schema exactly.** LangGraph's `Command(resume=...)` updates state by key. Typos silently corrupt state.

13. **Subgraph interrupts are still parent interrupts from the API's POV.** Resume with `Command(resume=...)` on the parent's thread — LangGraph routes to the right place.

14. **Stale browser tabs cause 409 conflicts.** Always check `app.aget_state(config).next` before resuming.

### 18.7 Re-runs and versioning

15. **Re-runs (v2) are not in scope yet but design state for them.** The `version` field is everywhere for a reason. When v2 happens, filter all queries by version. Don't hardcode `version=1` anywhere.

16. **The "more_questions" branch re-enters Discovery from `route_review_2_node`.** The subgraph's `prioritize_questions_node` runs again on the now-richer state. This works because already-asked questions are in `qa_history`. Test this flow explicitly.

### 18.8 Persistence

17. **Use JSONB, not TEXT, for all `*_json` and `metadata` columns.** You'll want to query into them.

18. **PostgresSaver is mandatory for production.** In-memory checkpointer = lose state on restart = furious users mid-Stage-2.

19. **Test by checkpointing mid-flow and resuming from a different process.** Catches state-serialization bugs early — Pydantic models that don't pickle, datetime objects that lose timezone.

20. **The checkpointer table can grow large.** Add TTL/archival policy for terminal threads.

---

## 19. Build Order

The CLI-first pattern: each layer is independently testable. You can demo a fully working agent on day 8 by typing into a terminal.

| Day | Deliverable | Test |
|---|---|---|
| **0** | Docker Compose up: Postgres+pgvector, Redis, MinIO. Run init SQL. Bootstrap MinIO buckets. Lock contracts in `docs/contracts.md`. | `docker compose ps` shows all healthy; `psql -c "SELECT 1"` works; `mc ls local/` shows both buckets |
| **1** | `shared/state_types.py` — every TypedDict, Pydantic schema. `shared/postgres.py`, `shared/llm_factory.py`. | Round-trip serialization through PostgresSaver |
| **2** | `ingestion/` package end-to-end | CLI: `python -m bra.cli ingest sample.pdf` produces ParsedDocument |
| **3** | `rag/` package — chunkers, embedder, writer, retriever | CLI: `python -m bra.cli rag-test "query"` returns chunks |
| **4-5** | Analyser subgraph | Standalone invoke with fake parsed_documents → AnalyserResult |
| **6-7** | Discovery subgraph | Run with simulated answers from YAML fixture → final markdown |
| **8** | Parent graph composition | Mount both subgraphs. Run end-to-end with simulated approval & answers via CLI. First touch the checkpointer. |
| **9** | Streaming layer (`runner/`) | `astream_events` → Redis pub/sub → mock WS logger |
| **10-11** | FastAPI routes + WebSocket (no auth) | Test with curl + dumb HTML page |
| **12** | Approved-doc RAG indexing + artifact export | Final two parent nodes; verify exports land in MinIO `bra-exports` |
| **13+** | Prompt tuning + edge cases | Failed parse, LLM timeout, malformed answer payload, etc. |

**Demoable milestones:**
- Day 0: Local infra running
- Day 5: Analyser subgraph standalone (CLI)
- Day 7: Discovery subgraph standalone (CLI)
- Day 8: Full pipeline (CLI)
- Day 11: Full pipeline via API + WebSocket
- Day 12: End-to-end with downloadable artifacts

---

## 20. Pre-Build Contracts to Lock

Before writing any code on Day 1, write `docs/contracts.md` with these locked:

1. **Every TypedDict in `shared/state_types.py`** — exact field names and types
2. **The 8 scoring criteria and their weights** (BRD specifies — write Pydantic for it)
3. **MoSCoW classification rules** (any heuristics, e.g., "explicitly stated as required = must")
4. **The 10-question hard cap policy** (or whatever number)
5. **Exact JSON schema of `user_edits_payload`** for review_1 and review_2
6. **Exact WS event taxonomy** with payload schemas (§14.4)
7. **Exact `llm_config` table shape** and which agent_ids exist (§13)
8. **The `expires_at` policy** for working_chunks (default 30d post-activity)
9. **Versioning rules** for requirement_nodes (insert new, never delete)
10. **Discovery termination conditions** (§8, §12.5)

These are your contracts. Once locked, you can build subgraphs in parallel without conflicts and the API/frontend teams can build in parallel against stable schemas.

---

## Appendix A — Technology Stack Summary

| Concern | Pick | Why |
|---|---|---|
| Orchestration | LangGraph | BRD-mandated; correct choice |
| Checkpointer | `PostgresSaver` | Survives restarts |
| LLM SDK | LangChain wrappers | Per-agent provider switching |
| PDF parsing | PyMuPDF | Fast, handles edge cases |
| DOCX parsing | python-docx | Standard |
| PPTX parsing | python-pptx | Standard |
| XLSX parsing | openpyxl | Standard |
| Vision (images in docs) | Claude or GPT-4o vision | Describe diagrams, don't OCR |
| Embeddings | `text-embedding-3-small` (1536d) | Cost/quality sweet spot |
| Vector store | pgvector | BRD-mandated; co-located with PG |
| Hybrid search | pgvector + tsvector + RRF | Better than either alone |
| Streaming | `astream_events(version="v2")` | Per-token + per-event |
| Pub/sub | Redis | Decouple graph from WS handlers |
| Background work | ARQ or FastAPI BackgroundTasks | Ingestion can be slow |
| Schema validation | Pydantic v2 + `with_structured_output()` | Prevents hallucinated JSON shape |
| JSON patches | `jsonpatch` library | RFC 6902 compliant |
| Templating | Jinja2 | For finalize_doc_node |
| PDF render | WeasyPrint | HTML→PDF, good output |
| DOCX render | python-docx | Same lib used for parsing |
| Object store | MinIO (Docker) | S3-compatible; same SDK code works against AWS S3 later |
| Observability | LangSmith | BRD-mandated; just turn it on |
| Testing | Pytest + pytest-asyncio | Standard |

---

## Appendix B — Glossary

| Term | Meaning |
|---|---|
| **Parent graph** | The top-level LangGraph orchestrating ingestion, RAG, approvals, exports, and the two subgraphs |
| **Subgraph** | A compiled LangGraph mounted as a node in the parent (Analyser, Discovery) |
| **Working chunks** | Pre-approval, TTL'd raw doc chunks for in-flight retrieval |
| **Requirement nodes** | Post-approval, permanent, versioned chunks of the approved analysis |
| **Interrupt** | A pause point where the graph waits for user input via `Command(resume=...)` |
| **Reducer** | The function (e.g. `add`) that combines parallel writes to a state field |
| **Checkpointer** | The persistence layer that saves state at every node transition |
| **MoSCoW** | Must Have / Should Have / Could Have / Won't Have prioritization framework |
| **RRF** | Reciprocal Rank Fusion — algorithm to combine multiple ranking sources |
| **HNSW** | Hierarchical Navigable Small World — pgvector's approximate-NN index |
| **TSV** | Postgres tsvector — full-text search column |
| **Delta change** | An audit-logged mutation to `analyser_output` (from enrichment, QA, or user edit) |

---

**End of document.**

*Last updated: April 27, 2026 — added local Docker infrastructure section, removed authentication scaffolding, expanded State Schemas with rationale, expanded Node-by-Node Specification with pseudocode blueprints.*
