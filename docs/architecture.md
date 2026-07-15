# JARVIS OS Architecture

**Version:** 2.0  
**Last Updated:** 2026-07-15  
**Status:** Core + Voice + Skills foundation

---

## 1. Guiding Principles

1. **Offline-first** — Core intelligence runs locally.
2. **One command → one (or more) skills** — natural language drives actions.
3. **Capability-based Security** — Default-deny + explicit consent.
4. **Clean Architecture** — outer layers depend on inner.
5. **Modularity** — voice, vision, skills independently testable.
6. **SOLID + Type Safety** — Python 3.11+ with full type hints.

---

## 2. Cool system structure

```
┌──────────────────────────────────────────────────────────────┐
│  Electron Tray  ·  React HUD  ·  Voice Console (/console)    │
│  Global hotkey · Arc-reactor UI · Waveforms                  │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP / WebSocket (localhost)
┌────────────────────────────▼─────────────────────────────────┐
│  FastAPI Backend                                             │
│  routers: health · ai · voice · skills · memory · system     │
│  services: AI · Voice · Memory                               │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Agents                                                      │
│  Orchestrator: text → skill match → permissions → execute    │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Skills (the hands)                                          │
│  browser · apps · email* · media* · files* · calendar*       │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│  Core                                                        │
│  config · permissions · sandbox · audit · crypto             │
└──────────────────────────────────────────────────────────────┘

* = roadmap (see docs/ROADMAP.md)
```

### Repository layout

```
JARVIS-AI/
├── agents/           # Orchestrator (command → skills)
├── backend/          # FastAPI app, routers, services
├── core/             # Config + security foundation
├── skills/           # ★ One-command powers
│   ├── base.py
│   ├── registry.py
│   ├── browser.py    # YouTube, Gmail, search, URL
│   ├── apps.py       # Launch Chrome, VS Code, …
│   └── system_info.py
├── voice/            # Formant TTS + voice service
├── frontend/public/  # Voice + skills console UI
├── docs/
│   ├── architecture.md
│   ├── ROADMAP.md
│   └── assets/       # Logos + sample WAVs
├── tests/
└── scripts/
```

---

## 3. One-command data flow

```
"Open YouTube"
    → Console / Voice / POST /api/v1/skills/execute
    → AgentOrchestrator.match()
    → skills.browser.OpenYouTubeSkill
    → Permission.AUTOMATION_BROWSER
    → webbrowser.open("https://www.youtube.com")
    → TTS: "Opening YouTube, sir."
    → Audit log
```

---

## 4. Voice stack

| Layer | Now | Next |
|-------|-----|------|
| TTS | `jarvis-formant` (pure Python, audible) | Piper neural (British male) |
| STT | Web Speech API in console | faster-whisper local |
| Commands | Intent + skill router | LLM tool-calling |
| UI | `/console` Iron Man HUD | Full React + Electron |

---

## 5. Security model

- Default **deny**
- Each skill lists required `Permission`s
- Development auto-grants browser/app skills for UX
- Production: explicit grants + confirm for send/delete/shutdown
- Full audit trail

---

## 6. Module status

| Module | Status | Notes |
|--------|--------|-------|
| Core | ✅ | config, security, sandbox |
| Backend API | ✅ | health, ai, voice, skills, memory |
| Voice TTS | ✅ | formant engine (real audio) |
| Voice Console | ✅ | `/console` |
| Skills framework | ✅ | registry + orchestrator |
| Browser skills | ✅ | YouTube, Gmail, search, URL |
| Apps launch | ✅ | whitelist map |
| Email send | 🔜 | SMTP / Gmail OAuth |
| Piper voice | 🔜 | natural JARVIS tone |
| Electron shell | 🔜 | tray + hotkey |
| Vision | 🔜 | screenshot + OCR |

Full checklist: **[docs/ROADMAP.md](./ROADMAP.md)**

---

## 7. Branding

| Asset | Path |
|-------|------|
| Logo | `docs/assets/jarvis_logo.png` |
| Dark logo | `docs/assets/jarvis_logo_dark.png` |
| Icon | `docs/assets/jarvis_icon.png` |
| Welcome audio | `docs/assets/jarvis_welcome.wav` |

Colors: cyan `#00E5FF` · gold `#C9A227` · void `#05080F`

---

*At your service, sir.*
