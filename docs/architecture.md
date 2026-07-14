# JARVIS OS Architecture

**Version:** 1.0  
**Last Updated:** 2026-07-14  
**Status:** Foundation Complete (Core Module)

---

## 1. Guiding Principles

1. **Offline-first** — All core intelligence runs locally.
2. **Zero placeholders** — Every component is production-grade from day one.
3. **Capability-based Security** — Default-deny + explicit user consent.
4. **Clean Architecture** — Dependency rule: outer layers depend on inner.
5. **Modularity** — Each major domain (voice, vision, automation) is independently testable.
6. **SOLID + Type Safety** — Python 3.11+ with full type hints.

---

## 2. High-Level Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Electron Desktop Shell (UI + Tray + IPC)                   │
│  React + TypeScript Frontend                                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP + WebSocket (localhost)
┌────────────────────▼────────────────────────────────────────┐
│  FastAPI Backend (app.main)                                 │
│  • Routers (health, ai, voice, automation, system)          │
│  • Services (AgentOrchestrator, MemoryService, etc.)        │
│  • Dependency injection                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  Core Layer (immutable foundation)                          │
│  • config (Settings)                                        │
│  • security (PermissionManager, Sandbox, Audit, Crypto)     │
│  • exceptions                                               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  Domain Agents & Services                                   │
│  memory • voice • vision • automation • plugins             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Core Module (Completed - v1.0)

**Location:** `core/`

### 3.1 Configuration (`core/config`)

- `Settings`: Frozen Pydantic v2 root model
- Nested configs: `AIConfig`, `VoiceConfig`, `SecurityConfig`, etc.
- Environment: `JARVIS_*` prefix + `.env`
- Strong path safety + directory auto-creation
- Offline-first validation (Ollama must be localhost)

### 3.2 Security (`core/security`)

- **Permission System**: Capability-based (`Permission` enum)
- **PermissionManager**: Runtime grants, context managers, decorators
- **Sandbox**: Whitelisted subprocess execution with timeout + output limits
- **Crypto**: AES-GCM, Ed25519/RSA keygen, password hashing (Argon2 / PBKDF2)
- **AuditLogger**: Structured events + ring buffer + file sink

### 3.3 Exceptions

- `JarvisError` base
- Domain-specific: `SecurityError`, `PermissionDeniedError`, etc.

---

## 4. Data Flow (Example: Voice Command)

1. Electron / Frontend → FastAPI `/voice/transcribe`
2. Backend service calls `voice` module
3. `voice` module requests `Permission.VOICE_LISTEN`
4. PermissionManager + AuditLogger record action
5. If allowed → Whisper inference (local)
6. Result → LLM via Ollama (core AI)
7. Optional: `automation` agent triggered
8. All steps audited

---

## 5. Security Model

- Default: **Deny all**
- All privileged actions require explicit grant (UI or voice confirmation)
- Sandboxed execution for every external action
- No network access unless explicitly enabled
- Full tamper-evident audit trail
- Secrets never logged

---

## 6. Current Module Status

| Module           | Status          | Tests | Security Review | Docs |
|------------------|-----------------|-------|------------------|------|
| **Core**         | ✅ COMPLETE     | Pass  | Pass             | Full |
| Backend Skeleton | In Progress     | -     | -                | -    |
| Frontend         | Not Started     | -     | -                | -    |
| ...              | ...             | ...   | ...              | ...  |

---

## 7. Next Steps (Master Loop)

1. Backend Core (FastAPI + routers + DI)
2. Memory Layer
3. AI Service + Ollama integration
4. Voice pipeline
5. etc.

See `README.md` for current development status.
