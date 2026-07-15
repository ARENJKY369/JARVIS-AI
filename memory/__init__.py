"""
JARVIS OS - Memory Layer
========================

Long-term memory and vector storage for semantic recall.

Components:
- VectorStore: ChromaDB / LanceDB interface
- MemoryService: High-level memory operations
"""

from .vector_store import VectorStore, get_vector_store

__all__ = ["VectorStore", "get_vector_store"]
