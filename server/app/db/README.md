# `app/db/` — Database layer

Thin SQLAlchemy 2.x setup. SQLite by default (`bra_tool.db` in the server
folder); override `DATABASE_URL` to point at local Postgres when you want
pgvector support.

## Files

| File | Purpose |
|------|---------|
| `base.py` | The one-and-only `Base = DeclarativeBase()`. Kept in its own file so model modules don't pull in `session.py` (and by extension `settings`) at import time — important for Alembic autogeneration. |
| `session.py` | Creates the `engine` from `settings.database_url` and a `SessionLocal` sessionmaker. Exposes `get_db()` — the FastAPI dependency used by route handlers. Adds `check_same_thread=False` automatically when the URL is SQLite. |
| `models/__init__.py` | Imports every ORM model so `Base.metadata` is fully populated at startup (used by `Base.metadata.create_all(bind=engine)` in `main.py::lifespan`). |

## Models (`models/`)

| File | Table | Mirrors BRD |
|------|-------|-------------|
| `project.py` | `projects` | §8.1 |
| `document.py` | `documents` (uses `local_path`, not `s3_key`) | §8.1 adapted for local dev |
| `stage_output.py` | `stage_outputs` | §8.1 |
| `discovery_qa.py` | `discovery_qa` | §8.1 |
| `change_event.py` | `change_events` | §10 |
| `version.py` | `project_versions` | §10 |
| `llm_config.py` | `llm_configs` | §8.1 |

Adding a new model:
1. create `models/<name>.py` with a class inheriting from `Base`
2. import it in `models/__init__.py`
3. run the app once — SQLite will auto-create the table via `Base.metadata.create_all`
