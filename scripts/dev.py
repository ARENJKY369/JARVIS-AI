#!/usr/bin/env python3
"""
JARVIS OS - Development Launcher
================================

Starts both backend and frontend in development mode.

Usage:
    python scripts/dev.py
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run_backend(port: int = 8000):
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--reload", "--port", str(port)],
        cwd=ROOT,
    )


def run_frontend():
    # On Windows, we must use shell=True to find and run batch files/scripts like npm.
    use_shell = sys.platform == "win32"
    return subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=ROOT / "frontend",
        shell=use_shell,
    )


def main():
    parser = argparse.ArgumentParser(description="JARVIS OS Dev Launcher")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--no-frontend", action="store_true", help="Only start backend")
    parser.add_argument("--no-backend", action="store_true", help="Only start frontend")
    args = parser.parse_args()

    procs = []

    if not args.no_backend:
        print("[dev] Starting backend...")
        procs.append(run_backend(args.backend_port))
        time.sleep(2)

    if not args.no_frontend:
        print("[dev] Starting frontend...")
        procs.append(run_frontend())

    print("[dev] Press Ctrl+C to stop all services")

    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("\n[dev] Shutting down...")
        for p in procs:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        print("[dev] Goodbye.")


if __name__ == "__main__":
    main()
