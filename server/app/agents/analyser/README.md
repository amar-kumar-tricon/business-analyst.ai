# Analyser Agent — Stage 1

## Files
| File | Purpose |
|------|---------|
| `agent.py` | `analyser_node(state)` — the LangGraph node. Reads `uploaded_documents` + `additional_context`, scores the document, conditionally enriches, returns a structured `AnalyserResult` which is written back to `state.analyser_output`. |
| `prompts.py` | Prompt templates only — `SYSTEM`, `SCORING_RUBRIC`, `ENRICHMENT`. Change wording here; no code changes needed. |
| `tools.py` | Pure helpers: `SCORING_WEIGHTS` (BRD §4.2), `score_document`, `enrich`, `classify_moscow`, `extract_risks`, `recommend_team`. Unit-testable without an LLM. |

## How to extend
- **New scoring criterion** → add to `SCORING_WEIGHTS` in `tools.py` (must sum to 1.0).
- **New output field** → add to `schemas/analyser.py::AnalyserResult`, then populate it in `agent.py`.
- **Better enrichment** → rewrite `tools.enrich` to call the LLM with richer context.
