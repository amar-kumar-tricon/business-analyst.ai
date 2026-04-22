# `app/core/` — Cross-cutting primitives

Tiny, boring helpers used everywhere else. Nothing here imports from `api/`,
`agents/`, or `services/` — it's the bottom of the dependency stack.

## Files

| File | Why it exists |
|------|---------------|
| `config.py` | Single source of truth for environment settings. Loads `.env` into a typed `Settings` object via `pydantic-settings`. Import `settings` from here — **never** call `os.getenv()` directly anywhere else in the codebase. Add a new env var by adding a typed field and documenting it in `server/.env.example`. |
| `logging.py` | One-line `configure_logging()` wired into the app's startup lifecycle in `main.py`. Tames noisy third-party loggers and standardises the format. Swap to `structlog` here if you ever need JSON logs for a log aggregator. |
