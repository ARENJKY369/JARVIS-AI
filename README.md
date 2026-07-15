# JARVIS OS
**J.A.R.V.I.S. - Just A Rather Very Intelligent System**

Professional, offline-first AI Desktop Operating Assistant built for production use.

Inspired by the Iron Man cinematic interface — JARVIS OS brings a sophisticated, voice-controlled, multimodal AI companion directly to your desktop.

**Version:** 1.0.0  
**Status:** In active autonomous development (Master Loop)  
**License:** MIT (see LICENSE)  
**Offline-first:** 100% local by default (Ollama + Whisper + Piper + SQLite + Vector DB)

---

## 🚀 Vision

A production-quality, secure, extensible desktop AI operating system that:
- Runs completely offline
- Understands natural language + voice + vision
- Automates complex workflows safely
- Learns and adapts over time
- Provides a beautiful, cinematic UI
- Is fully modular and plugin-driven

## ✨ Key Features (Roadmap)

- **Core AI Engine**: Local LLM (Ollama) with tool-calling and long-term memory
- **Voice Interface**: Real-time STT (Whisper) + TTS (Piper) with Iron Man voice profile
- **Vision System**: Screen understanding, OCR, object detection via OpenCV + local models
- **Automation Engine**: Safe browser + desktop automation (Playwright + PyAutoGUI)
- **Memory & Learning**: Vector + relational persistence with semantic recall
- **Plugin System**: First-class extensibility
- **Electron Desktop App**: Native cross-platform experience
- **Security**: Sandboxed execution, permission system, audit logs
- **Developer Friendly**: Clean APIs, full test coverage, extensive docs

---

## 🏗️ Architecture Overview

```
JarvisOS/
├── backend/          # FastAPI Python backend (core intelligence)
├── frontend/         # React + TypeScript + Tailwind SPA
├── electron/         # Electron desktop shell (main + renderer)
├── agents/           # Domain-specific autonomous agents
├── core/             # Shared Python primitives (config, security, memory)
├── memory/           # Vector + relational memory layer
├── voice/            # STT / TTS services
├── vision/           # Computer vision pipeline
├── automation/       # Safe automation primitives
├── browser/          # Browser automation agent
├── coding/           # Code generation & execution agent
├── learning/         # Continuous learning & fine-tuning
├── plugins/          # Dynamic plugin loader & registry
├── security/         # Permissions, sandbox, audit
├── config/           # Centralized configuration
├── models/           # Downloaded local AI models
├── database/         # SQLite + LanceDB / Chroma
├── tests/            # Comprehensive test suites
├── docs/             # Architecture, API, guides
├── scripts/          # Dev, build, install utilities
└── installer/        # Cross-platform installer
```

**Principles Applied:**
- Clean Architecture + SOLID
- Dependency Injection
- Modular independence (each agent/service can run standalone)
- Async-first (where beneficial)
- Offline-first, zero cloud dependency for core features
- Type-safe Python (3.11+) + TypeScript
- Comprehensive validation at every layer

See `docs/architecture.md` for deep technical details.

---

## 📦 Tech Stack

| Layer          | Technology                          |
|----------------|-------------------------------------|
| Backend        | Python 3.11, FastAPI, Uvicorn, Pydantic, SQLAlchemy |
| AI / LLM       | Ollama (local), LangChain (local adapters) |
| Voice          | faster-whisper, piper-tts, sounddevice |
| Vision         | OpenCV, pytesseract, easyocr (local) |
| Automation     | Playwright, pyautogui, pynput |
| Memory         | SQLite, chromadb / lancedb (local vector) |
| Frontend       | React 18, TypeScript, Tailwind CSS, Vite |
| Desktop        | Electron 30+, electron-builder |
| Testing        | pytest, vitest, playwright (e2e) |
| Security       | pydantic-settings, cryptography, sandboxing |

---

## 🛠️ Quick Start (Development)

### Prerequisites
- Python >= 3.11
- Node.js >= 20
- Git
- (Optional for full features) Ollama installed + `llama3.2` or `phi3` pulled

### 1. Clone & Setup

```bash
git clone https://github.com/ARENJKY369/JARVIS-AI.git
cd JARVIS-AI

# Python environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Node setup — Frontend
cd frontend && npm install && cd ..

# Node setup — Electron (optional)
cd electron && npm install && cd ..

# Copy environment config
cp .env.example .env
```

### 2. Start Components (Development Mode)

**Option A: One-command dev launcher**
```bash
python scripts/dev.py
```

**Option B: Manual terminals**
```bash
# Terminal 1: Backend
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend dev server
cd frontend
npm run dev

# Terminal 3: Electron (optional)
cd electron
npm run start
```

The frontend will be available at `http://localhost:5173` and proxies API calls to the backend at `http://127.0.0.1:8000`.

### 3. Run Full Validation (after changes)

```bash
# From root
python scripts/validate.py
pytest tests/
npm --prefix frontend run test
```

### 3. Build for Production

```bash
# Build frontend
cd frontend
npm run build

# Run production backend (serves static frontend)
cd ..
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 4. Build Desktop App (Electron)

```bash
cd electron
npm run build
```

Full installation instructions: `docs/guides/installation.md`

---

## 🧪 Development Workflow (Master Autonomous Loop)

This project follows a strict **autonomous engineering loop**:
1. Analyze full state
2. Prioritize ONE module
3. Design
4. Implement production-grade code
5. Validate (lint, type, syntax)
6. Test (unit + integration)
7. Security review
8. Optimize
9. Document
10. Commit only when 100% green

**Never** claim completion without passing all gates.

---

## 🎨 Branding & Assets

Professional logo and Iron Man-style voice samples are located in:
- `docs/assets/jarvis_logo.png`
- `docs/assets/jarvis_logo_dark.png`
- `docs/assets/jarvis_welcome.mp3` (and more)

---

## 🔒 Security & Privacy

- All AI runs locally by default.
- No telemetry.
- Sandboxed automation.
- Explicit user consent for any privileged operation.
- Full audit logging.

---

## 📜 License

MIT License. See `LICENSE` file.

---

## 🤝 Contributing

See `docs/guides/developer_guide.md`

Current status: Following Master Loop — building one module at a time.

---

**JARVIS OS** — "At your service, sir."

*Built autonomously by the Arena engineering agent.*
