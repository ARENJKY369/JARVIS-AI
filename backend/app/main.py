"""
JARVIS OS - FastAPI Application Factory
=======================================

Production-grade FastAPI backend for JARVIS OS.

Responsibilities:
- Application factory (create_app)
- Lifespan events (startup / shutdown)
- Global exception handlers
- CORS (strict localhost only)
- Request logging & correlation IDs
- Dependency injection setup
- Router registration
- Health & system endpoints

This module is the entry point for:
    uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

Design:
- Clean separation: routers → services → core
- All privileged endpoints require permission checks
- Structured logging via loguru
- Graceful shutdown
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from loguru import logger

from core.config import get_settings, Settings
from core.security import get_permission_manager, get_audit_logger, AuditEventType
from core.exceptions import JarvisError, SecurityError

from .dependencies import get_settings_dependency, get_permission_manager_dependency

settings: Settings = get_settings()
permission_manager = get_permission_manager()
audit_logger = get_audit_logger()

# Pre-import routers at module level to guarantee registration
# (prevents any circular import issues)
try:
    from backend.routers import health_router, system_router
except ImportError:
    health_router = None
    system_router = None

try:
    from backend.routers.ai import router as ai_router
except ImportError:
    ai_router = None

try:
    from backend.routers.voice import router as voice_router
except ImportError:
    voice_router = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # Startup
    logger.info("🚀 JARVIS OS Backend starting...")
    logger.info(f"   Version: {settings.version}")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Offline mode: {settings.is_offline_mode()}")
    logger.info(f"   AI Model: {settings.ai.default_model}")

    # Warm up voice engine so first speak is instant
    try:
        from backend.services.voice_service import get_voice_service

        vs = get_voice_service()
        await vs.initialize()
        logger.info("   Voice: jarvis-formant TTS ready (offline)")
    except Exception as exc:
        logger.warning(f"   Voice warmup skipped: {exc}")

    audit_logger.log_event(
        AuditEventType.SYSTEM_START,
        details={
            "component": "backend",
            "version": settings.version,
            "environment": settings.environment,
        },
    )

    yield

    # Shutdown
    logger.info("🛑 JARVIS OS Backend shutting down...")
    audit_logger.log_event(
        AuditEventType.SYSTEM_SHUTDOWN,
        details={"component": "backend"},
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="JARVIS OS API",
        description="Professional offline-first AI Desktop Operating Assistant API",
        version=settings.version,
        docs_url="/docs" if settings.debug or settings.environment != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # ======================
    # Middleware
    # ======================

    # Strict CORS - only localhost for desktop app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",  # Vite dev
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "file://",  # Electron
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Request ID + timing middleware
    @app.middleware("http")
    async def add_correlation_id(request: Request, call_next: Any) -> Any:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        request.state.request_id = request_id
        request.state.start_time = start_time

        logger.bind(request_id=request_id).debug(
            f"→ {request.method} {request.url.path}"
        )

        response = await call_next(request)

        duration = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration:.2f}ms"

        logger.bind(request_id=request_id).info(
            f"← {request.method} {request.url.path} {response.status_code} ({duration:.1f}ms)"
        )
        return response

    # ======================
    # Exception Handlers
    # ======================

    @app.exception_handler(JarvisError)
    async def jarvis_exception_handler(request: Request, exc: JarvisError) -> JSONResponse:
        logger.error(f"JARVIS error: {exc}")
        audit_logger.log_event(
            AuditEventType.SYSTEM_START,  # placeholder; better types later
            details={"error": exc.code, "message": exc.message},
            success=False,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(SecurityError)
    async def security_exception_handler(request: Request, exc: SecurityError) -> JSONResponse:
        logger.warning(f"Security violation: {exc}")
        audit_logger.log_event(
            AuditEventType.PERMISSION_DENIED,
            details={"error": str(exc)},
            success=False,
        )
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "SECURITY_ERROR", "message": str(exc)},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        )

    # ======================
    # Dependency Overrides (for testing)
    # ======================
    # In production these are injected via Depends()

    # ======================
    # Routers — robust registration (guaranteed)
    # ======================
    routers_to_register = [
        ("backend.routers.health", "router", "/api/v1", ["Health"]),
        ("backend.routers.system", "router", "/api/v1", ["System"]),
        ("backend.routers.ai", "router", "/api/v1", ["AI"]),
        ("backend.routers.voice", "router", "/api/v1", ["Voice"]),
        ("backend.routers.memory", "router", "/api/v1", ["Memory"]),
        ("backend.routers.skills", "router", "/api/v1", ["Skills"]),
    ]

    for module_name, attr, prefix, tags in routers_to_register:
        try:
            mod = __import__(module_name, fromlist=[attr])
            router_obj = getattr(mod, attr)
            app.include_router(router_obj, prefix=prefix, tags=tags)
            logger.debug(f"Registered router: {module_name}")
        except Exception as e:
            logger.warning(f"Could not register {module_name}: {e}")

    # Also register root API info
    try:
        from backend.routers.root import router as root_router
        app.include_router(root_router, prefix="/api/v1", tags=["API"])
    except Exception as e:
        logger.warning(f"Root router not registered: {e}")

    # Root health for convenience
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.version,
            "status": "online",
            "offline": settings.is_offline_mode(),
            "voice_console": "/console",
        }

    # Serve the voice console UI (static SPA entry)
    try:
        from pathlib import Path
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse

        console_dir = Path(__file__).resolve().parents[2] / "frontend" / "public"
        if console_dir.is_dir():

            @app.get("/console", tags=["UI"], include_in_schema=False)
            async def voice_console():
                """JARVIS voice console — hear and command JARVIS."""
                return FileResponse(console_dir / "index.html")

            @app.get("/console_hud", tags=["UI"], include_in_schema=False)
            async def hud_console():
                """JARVIS Iron-Man HUD console — central reactor, custom operator name + avatar."""
                return FileResponse(console_dir / "console.html")

            app.mount(
                "/console-assets",
                StaticFiles(directory=str(console_dir)),
                name="console-assets",
            )
            logger.info(f"Voice console UI mounted at /console ({console_dir})")
    except Exception as e:
        logger.warning(f"Voice console UI not mounted: {e}")

    # Serve built React frontend in production (if present)
    if not settings.debug:
        try:
            from fastapi.staticfiles import StaticFiles

            frontend_dist = settings.base_dir / "frontend" / "dist"
            if frontend_dist.exists():
                app.mount(
                    "/",
                    StaticFiles(directory=str(frontend_dist), html=True),
                    name="frontend",
                )
        except Exception as e:
            logger.warning(f"Frontend dist not mounted: {e}")


    return app


# Default app instance for uvicorn / direct import
app = create_app()


# CLI entry point
def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Convenience entry for running the server."""
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=settings.debug,
        log_level=settings.logging.level.lower(),
    )


if __name__ == "__main__":
    run_server()
