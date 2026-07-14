"""
JARVIS OS - Backend Package
===========================

The central FastAPI backend powering JARVIS OS.

This package contains:
- FastAPI application factory
- API routers (health, system, ai, voice, automation, etc.)
- Service layer (AI, memory, agents)
- Pydantic models for request/response
- Dependency injection for shared core components

Design:
- Clean Architecture: routers → services → core
- Async-first where it makes sense
- Full type safety
- Production logging and error handling

The backend is intended to be run as:
    uvicorn backend.app.main:app --reload

Or via the jarvis CLI once fully implemented.
"""

__version__ = "1.0.0"
