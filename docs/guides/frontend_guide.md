# JARVIS OS — Frontend Guide

## Overview

The JARVIS OS frontend is a modern React 18 + TypeScript single-page application built with Vite and styled with Tailwind CSS. It provides a cinematic, Iron Man-inspired interface for interacting with the JARVIS AI backend.

## Tech Stack

- **Framework**: React 18
- **Language**: TypeScript
- **Bundler**: Vite
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Animations**: Framer Motion

## Project Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── .env.example
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── types/
    │   └── index.ts
    ├── hooks/
    │   └── useApi.ts
    └── components/
        ├── Header.tsx
        ├── Sidebar.tsx
        ├── ChatInterface.tsx
        ├── StatusPanel.tsx
        └── VoiceControl.tsx
```

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` and proxies `/api` to the backend at `http://127.0.0.1:8000`.

## Features

### Chat Interface
- Full conversational UI with JARVIS AI
- Real-time message streaming support (ready)
- Model and timing metadata display
- Auto-scrolling message history

### Status Panel
- Live system health monitoring
- AI engine status (Ollama / fallback)
- Voice subsystem status
- Permission matrix viewer

### Voice Control
- Microphone toggle for STT
- TTS playback for responses
- Visual feedback for active states

## Theming

The UI uses a custom dark theme inspired by the Iron Man JARVIS interface:
- Primary: `jarvis-*` (cyan/blue spectrum)
- Neutral: `iron-*` (grayscale)
- Background: near-black (`#0a0a0a`)

## Building

```bash
npm run build
```

Output goes to `frontend/dist/`. The FastAPI backend serves these static files automatically in production mode.
