"""
JARVIS OS - Memory Package
==========================

Lightweight local memory: contacts, preferences, drafts.
"""

from .contacts import ContactBook, get_contact_book

__all__ = ["ContactBook", "get_contact_book"]
