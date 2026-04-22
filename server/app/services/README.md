# `app/services/` — Business logic

Framework-free helpers. **No FastAPI, no SQLAlchemy models, no LangChain here.**
These modules are called by both route handlers and agent nodes.

## Files

| File | Why it exists |
|------|---------------|
| `local_storage.py` | Wraps filesystem I/O. `save_upload`, `read_upload`, `save_export`, `list_uploads`. All paths live under `settings.upload_dir` / `settings.export_dir`. Keeping boto3-or-local-fs behind this module means swapping to S3 in production is a one-file change. |
| `document_parser.py` | Turns uploaded files into plain text + tables + images. One `_parse_<ext>` function per format dispatched by `parse()`. Currently returns stubs — juniors implement each format using PyMuPDF / python-docx / python-pptx / openpyxl. |
| `embeddings.py` | `chunk_text` (word-based splitter — replace with token-based) and `embed_chunks` (async, delegates to `langchain_openai.OpenAIEmbeddings`). Used by the Analyser agent for pgvector-based semantic retrieval. |
| `diagram_service.py` | Syntax validators only — `validate_mermaid`, `validate_plantuml`. Heavy rendering lives in the browser (no Java JAR needed). |
| `export_service.py` | `to_pdf` (WeasyPrint) + `to_docx` (python-docx). Takes a stage output dict, returns raw bytes. HTTP concerns stay in `api/v1/export.py`. |
