"""RAG service backed by ChromaDB.

One collection per (project_id, version, kind). Chroma handles embedding,
storage, and similarity search. We just chunk the text and hand it over.

Embeddings: OpenAI `text-embedding-3-small` when an API key is set, otherwise
Chroma's bundled default model (runs locally, no API needed).
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from typing import Any

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
DEFAULT_TOP_K = 5


# ---------------------------------------------------------------------------
# Chroma client + embedding function (singletons)
# ---------------------------------------------------------------------------

_CHROMA_DIR = settings.export_dir / "chroma"
_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
_client = chromadb.PersistentClient(path=str(_CHROMA_DIR))


def _embedding_function():
    if settings.openai_api_key:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
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
    try:
        _client.delete_collection(name)
    except Exception:
        pass
    return _client.create_collection(name=name, embedding_function=_embedding_function())


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

    return ids, name


def build_approved_index(
    project_id: str,
    version: int,
    analyser_output: dict,
) -> tuple[list[str], str]:
    """Build a permanent collection from approved requirements + risks."""
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
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

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
        return []
    name = _collection_name(project_id, version, kind)
    try:
        collection = _client.get_collection(name=name, embedding_function=_embedding_function())
    except Exception:
        return []

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
    return out
