#!/usr/bin/env python3
"""
JARVIS OS - Production Run Script
=================================

Starts the complete JARVIS OS backend in a clean, production-grade way.

Usage:
    python scripts/run.py
    python scripts/run.py --port 8001 --host 127.0.0.1 --reload

Features:
- Beautiful startup banner (Iron Man style)
- Validates entire system before launch
- Graceful shutdown
- Proper logging
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
from core.config import get_settings

# Configure beautiful logging
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>JARVIS</cyan> | {message}",
    colorize=True,
)


def print_banner():
    banner = r"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗     ██████╗ ███████╗   ║
║   ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    ██╔═══██╗██╔════╝   ║
║   ██║███████║██████╔╝██║   ██║██║███████╗    ██║   ██║███████╗   ║
║   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║    ██║   ██║╚════██║   ║
║   ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║    ╚██████╔╝███████║   ║
║   ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝     ╚═════╝ ╚══════╝   ║
║                                                                  ║
║              JUST A RATHER VERY INTELLIGENT SYSTEM               ║
║                        OFFLINE-FIRST AI OS                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print("   Version: 1.0.0  |  Offline-first  |  Production Ready\n")


def validate_before_start():
    """Run quick validation before launching."""
    from scripts.validate import main as validate_main
    import io
    import contextlib

    # Capture validation output
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        code = validate_main()

    if code != 0:
        logger.error("Pre-flight validation failed. Aborting launch.")
        sys.exit(1)

    logger.success("Pre-flight validation passed.")


def main():
    parser = argparse.ArgumentParser(description="JARVIS OS Backend Launcher")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev only)")
    parser.add_argument("--skip-validate", action="store_true", help="Skip pre-flight validation")
    args = parser.parse_args()

    print_banner()

    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"AI Model: {settings.ai.default_model}")
    logger.info(f"Offline mode: {settings.is_offline_mode()}")

    if not args.skip_validate:
        validate_before_start()

    logger.info("Starting JARVIS OS API server...")

    try:
        import uvicorn
        from backend.app.main import app

        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
            access_log=False,
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
    except Exception as exc:
        logger.exception(f"Fatal error during startup: {exc}")
        sys.exit(1)
    finally:
        logger.info("JARVIS OS has shut down. Goodbye, sir.")


if __name__ == "__main__":
    main()
