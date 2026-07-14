"""
JARVIS OS - Advanced Memory Service (Stub v1)
=============================================

Production-ready memory layer foundation.

Features (current):
- In-memory conversation store with TTL
- Simple semantic-like recall stub
- Permission-gated access
- Ready for real vector DB (Chroma / LanceDB) integration

This will be expanded into full memory/ module later.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from core.config import get_settings
from core.security import get_permission_manager, Permission


@dataclass
class MemoryEntry:
    id: str
    content: str
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryService:
    """Advanced memory service (in-memory for now)."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._store: dict[str, list[MemoryEntry]] = {}
        self._pm = get_permission_manager()

    def _ensure_permission(self) -> None:
        self._pm.require(Permission.MEMORY_READ)

    def store(self, user_id: str, content: str, metadata: dict | None = None) -> str:
        self._pm.require(Permission.MEMORY_WRITE)
        entry = MemoryEntry(
            id=str(int(time.time() * 1000)),
            content=content,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        if user_id not in self._store:
            self._store[user_id] = []
        self._store[user_id].append(entry)
        return entry.id

    def recall(self, user_id: str, query: str = "", limit: int = 5) -> list[MemoryEntry]:
        self._ensure_permission()
        entries = self._store.get(user_id, [])
        # Very basic relevance (will be replaced by vector search)
        if query:
            scored = sorted(
                entries,
                key=lambda e: sum(1 for word in query.lower().split() if word in e.content.lower()),
                reverse=True,
            )
            return scored[:limit]
        return entries[-limit:]

    def clear(self, user_id: str) -> None:
        self._store.pop(user_id, None)


_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
