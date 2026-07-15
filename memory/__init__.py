"""
JARVIS OS - Memory Package
==========================

Local memory: contacts, preferences, drafts, and vector store.
"""

from .contacts import ContactBook, get_contact_book

try:
    from .vector_store import VectorStore, get_vector_store
except Exception:  # optional if chromadb missing at import time
    VectorStore = None  # type: ignore
    get_vector_store = None  # type: ignore

__all__ = [
    "ContactBook",
    "get_contact_book",
    "VectorStore",
    "get_vector_store",
]
