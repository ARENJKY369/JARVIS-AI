#!/usr/bin/env python3
"""
JARVIS OS - Master Validation Script
====================================

Runs full production validation:
- Syntax / import checks
- Configuration loading
- Security subsystem
- Backend API full smoke test
- All routers + services

Exit code 0 = production ready
"""

import sys
import traceback
from pathlib import Path

# Ensure project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

def main() -> int:
    print("=" * 60)
    print("JARVIS OS - PRODUCTION VALIDATION")
    print("=" * 60)

    errors = []

    # 1. Core imports
    print("\n[1/6] Core imports...")
    try:
        from core.config import get_settings, _clear_settings_cache
        from core.security import get_permission_manager, Permission
        from core.security.audit import get_audit_logger
        print("  ✓ Core modules OK")
    except Exception as e:
        errors.append(f"Core import failed: {e}")
        traceback.print_exc()

    # 2. Settings
    print("\n[2/6] Configuration...")
    try:
        settings = get_settings()
        assert settings.app_name == "JARVIS OS"
        assert settings.ai.provider == "ollama"
        print(f"  ✓ Settings loaded (env={settings.environment})")
    except Exception as e:
        errors.append(f"Settings failed: {e}")

    # 3. Security
    print("\n[3/6] Security subsystems...")
    try:
        pm = get_permission_manager()
        pm.grant(Permission.AUTOMATION_EXECUTE, reason="validation")
        assert pm.has_permission(Permission.AUTOMATION_EXECUTE)
        audit = get_audit_logger()
        print("  ✓ PermissionManager + AuditLogger OK")
    except Exception as e:
        errors.append(f"Security failed: {e}")

    # 4. Backend app creation
    print("\n[4/6] Backend application factory...")
    try:
        from backend.app.main import create_app
        app = create_app()
        print(f"  ✓ FastAPI app created (title={app.title})")
    except Exception as e:
        errors.append(f"Backend create_app failed: {e}")
        traceback.print_exc()
        return 1

    # 5. Full API smoke test
    print("\n[5/6] Full API endpoint smoke test...")
    try:
        client = TestClient(app)

        endpoints = [
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/ready"),
            ("GET", "/api/v1/system/status"),
            ("GET", "/api/v1/system/permissions"),
            ("GET", "/api/v1/system/audit"),
            ("POST", "/api/v1/ai/chat", {"message": "Status report please"}),
            ("GET", "/api/v1/ai/models"),
            ("GET", "/api/v1/ai/health"),
            ("POST", "/api/v1/voice", {"action": "synthesize", "text": "Good evening, sir."}),
            ("GET", "/api/v1/voice/status"),
            ("GET", "/api/v1/voice/demo"),
            ("POST", "/api/v1/voice/speak", {"text": "JARVIS online."}),
            ("POST", "/api/v1/voice/command", {"text": "Hello JARVIS", "speak": True}),
            ("POST", "/api/v1/skills/execute", {"text": "ask chatgpt about quality", "dry_run": True}),
            ("POST", "/api/v1/voice/command", {"text": "open youtube and calculate 1+1", "speak": False}),
            ("GET", "/api/v1/skills"),
            ("GET", "/console"),
        ]

        for method, path, *payload in endpoints:
            data = payload[0] if payload else None
            if method == "GET":
                resp = client.get(path)
            else:
                resp = client.post(path, json=data)

            if resp.status_code >= 400:
                errors.append(f"{method} {path} → {resp.status_code}")
                print(f"  ✗ {method} {path} → {resp.status_code}")
            else:
                print(f"  ✓ {method} {path} → {resp.status_code}")

    except Exception as e:
        errors.append(f"API smoke test crashed: {e}")
        traceback.print_exc()

    # 6. Final summary + real audio verification
    print("\n[6/6] Final checks + audible TTS verification...")
    try:
        # Re-test one advanced AI call
        client = TestClient(app)
        r = client.post("/api/v1/ai/chat", json={"message": "Run a full system diagnostic."})
        assert r.status_code == 200
        print("  ✓ Advanced AI chat functional")

        # Ensure TTS is NOT the old silent stub
        import base64
        import wave
        import io
        import struct

        r = client.post("/api/v1/voice/speak", json={"text": "Good evening, sir. JARVIS online."})
        assert r.status_code == 200
        payload = r.json()
        raw = base64.b64decode(payload["audio_base64"])
        assert len(raw) > 2000, "Audio too small — still a stub?"
        with wave.open(io.BytesIO(raw), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            samples = struct.unpack("<" + "h" * (len(frames) // 2), frames)
            peak = max(abs(s) for s in samples)
        assert peak > 500, f"Audio is silent (peak={peak})"
        print(f"  ✓ Real audible TTS (peak amplitude={peak}, {payload['duration_ms']:.0f}ms)")
        print(f"  ✓ Engine: {payload.get('engine')}")
    except Exception as e:
        errors.append(f"Advanced AI / TTS verification failed: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    if errors:
        print("VALIDATION FAILED")
        for err in errors:
            print(f"  - {err}")
        print("=" * 60)
        return 1
    else:
        print("✅ ALL VALIDATIONS PASSED — PRODUCTION READY")
        print("   Voice console: http://127.0.0.1:8000/console")
        print("   Quality gate:  python scripts/quality_gate.py")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
