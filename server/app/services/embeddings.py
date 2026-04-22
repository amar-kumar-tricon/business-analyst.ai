"""
app.services.embeddings
=======================
Chunking + embedding generation. Stores vectors in pgvector (`document_chunks`).

TODO:
    * split parsed text into overlapping chunks (~500 tokens, 50-token stride)
    * call OpenAI `text-embedding-3-small` (1536-d) or local BGE
    * bulk insert into `document_chunks` with the vector column
"""
from __future__ import annotations


def chunk_text(text: str, *, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Naive word-based chunker — replace with a token-based splitter for production."""
    words = text.split()
    chunks: list[str] = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i : i + chunk_size]))
        i += chunk_size - overlap
    return chunks


async def embed_chunks(chunks: list[str]) -> list[list[float]]:  # pragma: no cover
    """Return one embedding vector per chunk. Implement with langchain_openai."""
    # from langchain_openai import OpenAIEmbeddings
    # return await OpenAIEmbeddings(model='text-embedding-3-small').aembed_documents(chunks)
    raise NotImplementedError
