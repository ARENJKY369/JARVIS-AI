"""
JARVIS OS - Vector Store
========================

Production-ready vector database interface.

Supports:
- ChromaDB (default)
- LanceDB (future)

Features:
- Semantic search
- Document ingestion
- Metadata filtering
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from core.config import get_settings


class VectorStore:
    """Vector database wrapper for semantic memory."""

    def __init__(self, persist_dir: Path | None = None) -> None:
        self.settings = get_settings()
        self.persist_dir = persist_dir or self.settings.get_vector_db_path()
        self._client: Any = None
        self._collection: Any = None

        if CHROMA_AVAILABLE:
            try:
                self._client = chromadb.PersistentClient(path=str(self.persist_dir))
                self._collection = self._client.get_or_create_collection("jarvis_memory")
                logger.success("VectorStore (ChromaDB) initialized")
            except Exception as e:
                logger.warning(f"ChromaDB init failed: {e}")
        else:
            logger.warning("ChromaDB not installed — vector search disabled")

    def add(self, texts: list[str], ids: list[str] | None = None, metadatas: list[dict] | None = None) -> None:
        if self._collection is None:
            logger.warning("Vector store unavailable — skipping add")
            return
        ids = ids or [f"doc_{i}" for i in range(len(texts))]
        self._collection.add(documents=texts, ids=ids, metadatas=metadatas)

    def query(self, query_text: str, n_results: int = 5) -> dict[str, Any]:
        if self._collection is None:
            return {"documents": [[]], "distances": [[]], "metadatas": [[]]}
        return self._collection.query(query_texts=[query_text], n_results=n_results)

    def count(self) -> int:
        if self._collection is None:
            return 0
        return self._collection.count()


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
