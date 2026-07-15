# JARVIS OS

<p align="center">
  <img src="docs/assets/jarvis_logo.png" alt="JARVIS OS Logo" width="280"/>
</p>

<p align="center">
  <strong>J.A.R.V.I.S. — Just A Rather Very Intelligent System</strong><br/>
  Professional, offline-first AI Desktop Operating Assistant
</p>

---

Inspired by the Iron Man cinematic interface — JARVIS OS brings a sophisticated, voice-controlled, multimodal AI companion directly to your desktop.

**Version:** 1.0.0  
**Status:** Production foundation (skills + voice + console)  
**License:** MIT (see LICENSE)  
**Offline-first:** Local by default (Ollama + formant/Piper TTS + SQLite)

---

## 🚀 Vision

A production-quality, secure, extensible desktop AI operating system that:
- Runs completely offline
- Understands natural language + voice + vision
- Automates complex workflows safely
- Learns and adapts over time
- Provides a beautiful, cinematic UI
- Is fully modular and plugin-driven

## ✨ Key Features
- **Core AI Engine**: Local LLM (Ollama) with tool-calling and long-term memory
- **Voice Interface**: Offline formant TTS with **two Iron-Man personas** — `jarvis` (classic butler) and `friday` (cool female companion) — optional Whisper STT / browser mic
- **One-command skills**: YouTube (+ **play any video URL**), open any **website/URL**, Gmail, ChatGPT research, email drafts, timers, notes, maps…
- **Mission planner**: Multi-step commands (`open youtube and set a timer…`)
- **ChatGPT "write → send → tell you"**: JARVIS opens ChatGPT with your prompt pre-filled + copied to clipboard, and **speaks the answer back to you**
- **Iron Man HUD console** (`/console_hud`): central arc-reactor, live audio visualizer, **custom operator name + profile picture**, JARVIS / FRIDAY persona picker
- **Iron Man personality**: Calm butler tone, always addresses you as "sir"
- **Security**: Sandboxed execution, permission system, audit logs
- **Developer Friendly**: Clean APIs, full test coverage, quality gate 10/10

---

## 🎙️ Voice profiles (JARVIS & FRIDAY only)

The console ships with **two** selectable personas — the Iron Man pairing:

| ID | Gender | Style |
|----|--------|--------|
| `jarvis` | Male | Classic deep British butler (default Iron Man tone) |
| `friday` | Female | Cool measured AI companion |

In the console: pick a persona → **Preview voice** → send commands.
API: `GET /api/v1/voice/voices` · `POST /api/v1/voice/speak` with `"voice": "friday"`.
Default persona: set `JARVIS_UI_DEFAULT_VOICE=friday` (or `jarvis`) in `.env`.

---

## 🖥️ Consoles

**Classic console:** `http://127.0.0.1:8000/console`
**Iron Man HUD console:** `http://127.0.0.1:8000/console_hud`

The HUD shows a central arc-reactor, a live audio visualizer while JARVIS speaks, a **custom operator name** (from `JARVIS_UI_USER_NAME`) and your **profile picture** (from `JARVIS_UI_USER_AVATAR` — a path or URL), and a JARVIS / FRIDAY persona picker.

Set your operator identity in `.env`:
```bash
JARVIS_UI_USER_NAME=Tony
JARVIS_UI_USER_AVATAR=/absolute/path/to/me.png
# or a URL:
# JARVIS_UI_USER_AVATAR=https://example.com/me.jpg
```

---

## 🏗️ Architecture Overview

```
JARVIS-AI/
├── agents/           # Orchestrator + mission planner + personality
├── backend/          # FastAPI (ai, voice, skills, memory, system)
├── core/             # Config + security (permissions, sandbox, audit)
├── skills/           # ★ Powers: browser, apps, email, ChatGPT, utils…
├── voice/            # Multi-voice formant TTS + voice service
├── frontend/public/  # Voice + skills console → http://127.0.0.1:8000/console
├── docs/             # architecture · ROADMAP · QUALITY · assets (logo)
├── tests/ · scripts/
└── (next) electron/ vision/ plugins/
```

**One-command examples (working now):**
- `Open YouTube` / `Open YouTube search lo-fi`
- `Open Gmail` · `open whatsapp`
- `ask chatgpt about machine learning`
- `help me write a cover letter`
- `email demo@example.com saying Hello from JARVIS`
- `open youtube and set a timer for 5 minutes` (multi-step mission)
- `System status` · `What time is it?`

**Setup guides:** [`docs/guides/email_and_voice.md`](docs/guides/email_and_voice.md) · [`.env.example`](.env.example)  
**Roadmap:** [`docs/ROADMAP.md`](docs/ROADMAP.md) · **Architecture:** [`docs/architecture.md`](docs/architecture.md)  
**Quality:** [`docs/QUALITY.md`](docs/QUALITY.md) · **Iron Man scope:** [`docs/IRON_MAN_OS.md`](docs/IRON_MAN_OS.md)

---

## 📦 Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Backend        | Python 3.11, FastAPI, Uvicorn, Pydantic, SQLAlchemy |
| AI / LLM       | Ollama (local) |
| Voice          | jarvis-formant (multi-voice), optional piper-tts, faster-whisper |
| Memory         | SQLite, contacts JSON |
| Frontend       | Voice console (HTML/CSS/JS), React planned |
| Testing        | pytest, quality_gate.py |
| Security       | pydantic-settings, cryptography, sandboxing |

---

## 🛠️ Quick Start (Development)

### Prerequisites
- Python >= 3.11
- Git
- (Optional) Ollama + `llama3.2` for deeper chat

### 1. Clone & Setup

```bash
git clone https://github.com/ARENJKY369/JARVIS-AI.git
cd JARVIS-AI

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start JARVIS

```bash
export PYTHONPATH=.
# Option A
python scripts/start_jarvis.sh

# Option B
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open the **Voice Console**:

**http://127.0.0.1:8000/console**

1. Choose a **Male** or **Female** voice  
2. Click **Preview voice**  
3. Click **▶ Hear JARVIS** or type a command  

### 3. Run Full Validation

```bash
python scripts/quality_gate.py   # must be 10/10 all dimensions
python scripts/validate.py
pytest tests/unit/ -o addopts= -q
```

---

## 🎨 Branding & Assets

<p align="center">
  <img src="docs/assets/jarvis_logo.png" alt="JARVIS Logo" width="200"/>
  &nbsp;&nbsp;
  <img src="docs/assets/jarvis_logo_dark.png" alt="JARVIS Dark Logo" width="200"/>
</p>

| Asset | Path |
|-------|------|
| Primary logo | `docs/assets/jarvis_logo.png` |
| Dark HUD logo | `docs/assets/jarvis_logo_dark.png` |
| App icon | `docs/assets/jarvis_icon.png` |
| Welcome audio | `docs/assets/jarvis_welcome.wav` |

Colors: cyan `#00E5FF` · gold `#C9A227` · void `#05080F`

---

## 🔒 Security & Privacy

- All AI runs locally by default.
- No telemetry.
- Sandboxed automation.
- Explicit user consent for privileged operations.
- Full audit logging.

---

## 📜 License

MIT License. See `LICENSE` file.

---

**JARVIS OS** — *"At your service, sir."*
