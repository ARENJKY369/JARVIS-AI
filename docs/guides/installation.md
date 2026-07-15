# JARVIS OS — Installation Guide

## Prerequisites

- Python >= 3.11
- Node.js >= 20
- Git
- (Optional) Ollama installed locally

## Step 1: Clone Repository

```bash
git clone https://github.com/ARENJKY369/JARVIS-AI.git
cd JARVIS-AI
```

## Step 2: Python Backend

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

For full AI features:
```bash
pip install ollama chromadb numpy
```

For voice features:
```bash
pip install faster-whisper sounddevice piper-tts
```

## Step 3: Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

## Step 4: Configuration

```bash
cp .env.example .env
# Edit .env with your preferences
```

## Step 5: Run

Development mode:
```bash
python scripts/dev.py
```

Production mode:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000` in your browser.
