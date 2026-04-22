# `app/db/models/` — one file per table

See the parent [db/README.md](../README.md) for the overview.

| File | Class | Key columns | Notes |
|------|-------|-------------|-------|
| `project.py` | `Project` | `id, name, status, current_stage, version, created_at` | Top-level session entity. |
| `document.py` | `Document` | `id, project_id, filename, file_type, local_path, size_bytes, parsed_text, score` | `local_path` is a filesystem path under `settings.upload_dir`. |
| `stage_output.py` | `StageOutput` | `id, project_id, version, stage, output_json, edits_json, approved_at, created_at` | One row per (project, version, stage). |
| `discovery_qa.py` | `DiscoveryQA` | `id, project_id, question, answer, status` | Status: `pending / answered / deferred / na`. |
| `change_event.py` | `ChangeEvent` | `id, project_id, source_stage, description, reprocessed_stages, triggered_at` | Backs the `change_propagation` LangGraph node. |
| `version.py` | `ProjectVersion` | `id, project_id, version_number, snapshot_json, created_at` | Immutable snapshot created by `POST /finalize`. |
| `llm_config.py` | `LLMConfigRow` | `agent_id, provider, model_name, temperature, max_tokens` | One row per agent; unique on `agent_id`. |
