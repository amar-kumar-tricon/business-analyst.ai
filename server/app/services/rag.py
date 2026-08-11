"""RAG service backed by ChromaDB.

One collection per (project_id, version, kind). Chroma handles embedding,
storage, and similarity search. We just chunk the text and hand it over.

Embeddings: OpenAI `text-embedding-3-small` when an API key is set, otherwise
Chroma's bundled default model (runs locally, no API needed).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from hashlib import sha1
from typing import Any

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


log = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
DEFAULT_TOP_K = 5


# ---------------------------------------------------------------------------
# Chroma client + embedding function (lazy singletons)
# ---------------------------------------------------------------------------

_CHROMA_DIR = settings.export_dir / "chroma"
_client: chromadb.api.client.Client | None = None


def _get_client():
    """Lazily create the persistent Chroma client.

    Lazy init keeps module import cheap and lets us recover from a corrupted
    on-disk state (e.g. after uvicorn `--reload` killed the previous worker
    mid-write) by deleting the directory and rebuilding.
    """
    global _client
    if _client is not None:
        return _client
    _CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        _client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
    except Exception as e:
        log.warning("[rag] chroma init failed (%s) — wiping %s and retrying", e, _CHROMA_DIR)
        import shutil

        shutil.rmtree(_CHROMA_DIR, ignore_errors=True)
        _CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
    return _client


def _reset_client_after_corruption() -> None:
    """Drop the in-memory client + wipe the on-disk dir; next call rebuilds."""
    global _client
    log.warning("[rag] resetting corrupted chroma state at %s", _CHROMA_DIR)
    _client = None
    import shutil

    shutil.rmtree(_CHROMA_DIR, ignore_errors=True)
    _CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def _embedding_function():
    key = settings.openai_api_key
    if key and len(key) > 10:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=key,
            model_name="text-embedding-3-small",
        )
    return embedding_functions.DefaultEmbeddingFunction()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_chunk_id(project_id: str, text: str) -> str:
    """Stable 16-hex chunk id from project id + text content."""
    return sha1(f"{project_id}:{text}".encode("utf-8")).hexdigest()[:16]


def _collection_name(project_id: str, version: int, kind: str) -> str:
    return f"{project_id}_v{version}_{kind}"


def _reset_collection(name: str):
    client = _get_client()
    try:
        client.delete_collection(name)
    except Exception:
        pass
    try:
        return client.create_collection(name=name, embedding_function=_embedding_function())
    except chromadb.errors.InternalError as e:
        # Common cause: uvicorn --reload killed the previous worker mid-write,
        # leaving SQLite in a half-locked / readonly state. Wipe and retry once.
        log.warning("[rag] create_collection failed (%s) — recovering", e)
        _reset_client_after_corruption()
        return _get_client().create_collection(name=name, embedding_function=_embedding_function())


_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)


def _chunks_for_section(section: dict) -> list[str]:
    text = (section.get("content") or "").strip()
    if not text:
        return []
    if section.get("content_type") in {"table", "image_description"}:
        return [text]
    return _splitter.split_text(text)


# ---------------------------------------------------------------------------
# Index builders
# ---------------------------------------------------------------------------

def build_working_index(
    project_id: str,
    version: int,
    parsed_documents: list[dict],
) -> tuple[list[str], str]:
    """Chunk parsed sections and add them to a fresh Chroma collection."""
    log.info("[rag] build_working_index START project_id=%s parsed_docs=%d", project_id, len(parsed_documents))
    name = _collection_name(project_id, version, "working")
    collection = _reset_collection(name)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    seen: set[str] = set()

    for doc in parsed_documents:
        for section in doc.get("sections", []):
            for piece in _chunks_for_section(section):
                cid = build_chunk_id(project_id, piece)
                if cid in seen:
                    continue
                seen.add(cid)
                ids.append(cid)
                documents.append(piece)
                metadatas.append({
                    "file_name": doc.get("file_name") or "",
                    "section_heading": section.get("section_heading") or "",
                    "content_type": section.get("content_type") or "text",
                })

    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    log.info("[rag] build_working_index DONE collection=%s chunks=%d", name, len(ids))
    return ids, name


def build_approved_index(
    project_id: str,
    version: int,
    analyser_output: dict,
) -> tuple[list[str], str]:
    """Build a permanent collection from approved requirements + risks."""
    log.info("[rag] build_approved_index START project_id=%s", project_id)
    name = _collection_name(project_id, version, "approved")
    collection = _reset_collection(name)

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for req in analyser_output.get("functional_requirements") or []:
        text = (req.get("description") or "").strip()
        if not text:
            continue
        ids.append(build_chunk_id(project_id, f"req:{req.get('req_id')}:{text}"))
        documents.append(text)
        metadatas.append({
            "kind": "requirement",
            "id": req.get("req_id") or "",
            "moscow": req.get("moscow") or "",
        })

    for risk in analyser_output.get("risks") or []:
        text = (risk.get("description") or "").strip()
        if not text:
            continue
        ids.append(build_chunk_id(project_id, f"risk:{risk.get('risk_id')}:{text}"))
        documents.append(text)
        metadatas.append({
            "kind": "risk",
            "id": risk.get("risk_id") or "",
            "severity": risk.get("severity") or "",
            "category": risk.get("category") or "",
        })

    if ids:
        # Deduplicate by chunk id (LLM may produce duplicate entries)
        seen: set[str] = set()
        dedup_ids, dedup_docs, dedup_metas = [], [], []
        for i, cid in enumerate(ids):
            if cid not in seen:
                seen.add(cid)
                dedup_ids.append(cid)
                dedup_docs.append(documents[i])
                dedup_metas.append(metadatas[i])
        collection.add(ids=dedup_ids, documents=dedup_docs, metadatas=dedup_metas)

    log.info("[rag] build_approved_index DONE collection=%s records=%d", name, len(ids))
    return ids, name


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    file_name: str | None
    section_heading: str | None
    metadata: dict[str, Any]


def retrieve(
    project_id: str,
    version: int,
    kind: str,
    query: str,
    k: int = DEFAULT_TOP_K,
) -> list[RetrievedChunk]:
    """Top-k similar chunks from the project's Chroma collection."""
    query = (query or "").strip()
    if not query:
        log.info("[rag] retrieve SKIP empty query")
        return []
    name = _collection_name(project_id, version, kind)
    try:
        collection = _get_client().get_collection(name=name, embedding_function=_embedding_function())
    except Exception as e:
        log.warning("[rag] retrieve collection %s missing: %s", name, e)
        return []

    log.info("[rag] retrieve START collection=%s k=%d query_chars=%d", name, k, len(query))
    result = collection.query(query_texts=[query], n_results=k)
    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    out: list[RetrievedChunk] = []
    for i, cid in enumerate(ids):
        meta = metas[i] or {}
        out.append(
            RetrievedChunk(
                chunk_id=cid,
                content=docs[i],
                score=1.0 - float(distances[i]) if distances else 0.0,
                file_name=meta.get("file_name") or None,
                section_heading=meta.get("section_heading") or None,
                metadata=meta,
            )
        )
    log.info("[rag] retrieve DONE returned=%d", len(out))
    return out
