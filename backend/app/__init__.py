"""
JARVIS OS - Backend Application Package
=======================================

FastAPI application factory and core web server.

This package provides the production-grade API layer for JARVIS OS.

Exposed:
- create_app() factory (recommended for tests and deployment)
- app (default instance for uvicorn)

All routers, dependencies, and exception handlers live here.
"""

from .main import app, create_app

__all__ = ["create_app", "app"]
