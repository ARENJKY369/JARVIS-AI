"""
JARVIS OS - Contact Book
========================

Simple JSON-backed contacts so "email Mom" resolves to an address.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings


@dataclass
class Contact:
    name: str
    email: str | None = None
    phone: str | None = None
    aliases: list[str] | None = None
    notes: str = ""

    def matches(self, query: str) -> bool:
        q = (query or "").strip().lower()
        if not q:
            return False
        if q == self.name.lower() or q in self.name.lower():
            return True
        for a in self.aliases or []:
            if q == a.lower() or q in a.lower():
                return True
        if self.email and q in self.email.lower():
            return True
        return False


class ContactBook:
    """Persistent contact store under data/contacts.json."""

    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self.path = path or (settings.base_dir / settings.data_dir / "contacts.json")
        self._contacts: list[Contact] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._seed_defaults()
            self._save()
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._contacts = [
                Contact(
                    name=c["name"],
                    email=c.get("email"),
                    phone=c.get("phone"),
                    aliases=c.get("aliases") or [],
                    notes=c.get("notes") or "",
                )
                for c in raw.get("contacts", [])
            ]
        except Exception as exc:
            logger.warning(f"Contact book load failed: {exc}")
            self._seed_defaults()

    def _seed_defaults(self) -> None:
        """Starter aliases — user fills real emails via console or file."""
        self._contacts = [
            Contact(name="Mom", email=None, aliases=["mother", "mum", "mama"]),
            Contact(name="Dad", email=None, aliases=["father", "papa"]),
            Contact(name="Me", email=None, aliases=["myself", "self"]),
        ]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "contacts": [
                {
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "aliases": c.aliases or [],
                    "notes": c.notes,
                }
                for c in self._contacts
            ]
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def list(self) -> list[Contact]:
        return list(self._contacts)

    def find(self, query: str) -> Contact | None:
        q = (query or "").strip()
        if not q:
            return None
        # exact name first
        for c in self._contacts:
            if c.name.lower() == q.lower():
                return c
        for c in self._contacts:
            if c.matches(q):
                return c
        return None

    def resolve_email(self, who: str) -> tuple[str | None, str | None]:
        """
        Resolve a person or raw email to (display_name, email).
        Returns (None, None) if unknown.
        """
        who = (who or "").strip().strip("\"'")
        if not who:
            return None, None
        # Raw email?
        if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", who):
            return who, who
        contact = self.find(who)
        if contact and contact.email:
            return contact.name, contact.email
        if contact:
            return contact.name, None
        return who, None

    def upsert(
        self,
        name: str,
        *,
        email: str | None = None,
        phone: str | None = None,
        aliases: list[str] | None = None,
        notes: str = "",
    ) -> Contact:
        existing = self.find(name)
        if existing:
            if email is not None:
                existing.email = email
            if phone is not None:
                existing.phone = phone
            if aliases is not None:
                existing.aliases = aliases
            if notes:
                existing.notes = notes
            self._save()
            return existing
        c = Contact(name=name, email=email, phone=phone, aliases=aliases or [], notes=notes)
        self._contacts.append(c)
        self._save()
        return c

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "count": len(self._contacts),
            "contacts": [asdict(c) for c in self._contacts],
        }


_book: ContactBook | None = None


def get_contact_book() -> ContactBook:
    global _book
    if _book is None:
        _book = ContactBook()
    return _book


__all__ = ["Contact", "ContactBook", "get_contact_book"]
