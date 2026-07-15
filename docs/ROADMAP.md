# JARVIS OS — Advancement Roadmap

**Goal:** One voice/text command → real actions  
Examples: *“Open YouTube”*, *“Send email to Mom saying I’ll be late”*, *“What’s on my calendar?”*

**Version:** 2.0 plan  
**Last updated:** 2026-07-15

---

## 1. What you want (one-command actions)

| You say / type | What should happen |
|----------------|--------------------|
| Open YouTube | Browser opens youtube.com (or search) |
| Open Gmail / WhatsApp Web | Browser to that site |
| Send email to X saying Y | Compose + send (or draft) via Gmail API / SMTP |
| Play music / pause | OS media keys or Spotify |
| Set a timer for 10 minutes | Local timer + voice alert |
| Take a screenshot | Capture screen → save / describe |
| Search the web for … | Browser search |
| Open VS Code / Chrome | Launch desktop app |
| Remind me at 5pm … | Scheduled reminder |
| Summarize this page | Vision/OCR + AI |
| Lock my PC | OS lock command |

None of that is magic — it is **Intent → Skill → Permission → Action → Speak result**.

---

## 2. Things we must add (checklist)

### A. Brain (understand the command)

- [ ] **Intent router** — map free text to a skill (`open_url`, `send_email`, `launch_app`, …)
- [ ] **Slot filling** — extract entities: app name, URL, email address, message body, time
- [ ] **LLM tool-calling** — Ollama model returns structured JSON tools (not just chat)
- [ ] **Confirmation layer** — dangerous actions (“send email”, “delete file”) need “Are you sure, sir?”
- [ ] **Multi-step plans** — “email the report and open the meeting link” → ordered skill chain

### B. Hands (skills that do work)

| Skill module | One-command examples | Tech to add |
|--------------|----------------------|-------------|
| `skills/browser` | Open YouTube, Gmail, search | `webbrowser` / Playwright |
| `skills/email` | Send / draft email | SMTP or Gmail API + OAuth |
| `skills/apps` | Open Chrome, VS Code, Calculator | OS process launch (whitelist) |
| `skills/system` | Volume, lock, shutdown, battery | OS APIs / safe shell |
| `skills/media` | Play/pause, next track | media keys / Spotify API |
| `skills/files` | Open folder, find file | path-safe file ops |
| `skills/calendar` | What’s next / create event | Google Calendar / local ICS |
| `skills/clipboard` | Copy / read clipboard | pyperclip |
| `skills/timer` | Timer, alarm, reminder | asyncio scheduler |
| `skills/vision` | Screenshot, read screen | OpenCV + OCR |
| `skills/code` | Run snippet, explain error | sandboxed Python |
| `skills/web` | Fetch page summary | httpx + readability (opt-in network) |

### C. Security (so it doesn’t go rogue)

- [ ] Permission per skill (`BROWSER_OPEN`, `EMAIL_SEND`, `APP_LAUNCH`, …)
- [ ] **Allowlist** of URLs / apps / email domains
- [ ] Voice/UI **confirm** for send / pay / delete / shutdown
- [ ] Full **audit log** of every action
- [ ] Secrets in `.env` only (SMTP password, OAuth tokens) — never in code
- [ ] Network **off by default**; enable only for email/browser skills you choose

### D. Voice (hear a real JARVIS)

| Level | Engine | Sounds like | Needs |
|-------|--------|-------------|-------|
| Now | `jarvis-formant` (pure Python) | Robotic but audible | Nothing |
| Better | **Piper** local neural TTS | Natural offline male voice | Download voice model |
| Best cinematic | **XTTS / StyleTTS2** or cloned sample | Closest to movie JARVIS | GPU + consent for voice clone |
| Cloud option | ElevenLabs / Azure (opt-in) | Very human | API key + network |

Also add:

- [ ] Wake word: *“Hey JARVIS”* (openWakeWord / Porcupine)
- [ ] Continuous listen mode (push-to-talk + always-on optional)
- [ ] Interrupt / barge-in while speaking
- [ ] Emotion / rate control (“alert” vs “calm”)

### E. Ears (understand your speech)

- [ ] Browser Web Speech API (already in console) — good for Chrome
- [ ] **faster-whisper** local STT for desktop mic
- [ ] VAD (voice activity detection) so it doesn’t hear itself
- [ ] Noise suppression

### F. Face (UI / desktop shell)

- [ ] Voice Console (done: `/console`)
- [ ] Full **React + Tailwind** HUD (arc reactor, waveform, skill cards)
- [ ] **Electron** tray app (start with OS, global hotkey)
- [ ] Overlay HUD while you work
- [ ] Settings panel: permissions, voice, email, apps

### G. Memory

- [ ] Remember contacts (“Mom” → email address)
- [ ] Remember preferences (default browser, name, city)
- [ ] Conversation memory across sessions (SQLite + vectors)
- [ ] Skill result history

### H. Packaging

- [ ] One-click installer (Windows / macOS / Linux)
- [ ] `jarvis` CLI: `jarvis "open youtube"`
- [ ] Auto-start backend + tray
- [ ] Model downloader script (Whisper + Piper + Ollama pull)

---

## 3. Cool target structure (JARVIS OS)

```
JARVIS-AI/
├── backend/                 # FastAPI brain
│   ├── app/                 # factory, lifespan, middleware
│   ├── routers/             # HTTP API (ai, voice, skills, system…)
│   └── services/            # orchestrator, ai, voice, memory adapters
│
├── core/                    # shared foundation (no business skills)
│   ├── config/              # Settings, env
│   ├── security/            # permissions, sandbox, audit, crypto
│   └── exceptions/
│
├── agents/                  # high-level planners
│   ├── orchestrator.py      # Intent → plan → skills
│   ├── conversation.py
│   └── planner.py           # multi-step tool plans
│
├── skills/                  # ★ ONE FOLDER PER POWER ★
│   ├── base.py              # Skill interface (name, permissions, run)
│   ├── registry.py          # auto-discover skills
│   ├── browser/
│   ├── email/
│   ├── apps/
│   ├── system/
│   ├── media/
│   ├── files/
│   ├── calendar/
│   ├── timer/
│   └── web/
│
├── voice/                   # STT + TTS + wake word
│   ├── tts.py               # formant (now) + piper adapter
│   ├── stt.py
│   ├── wakeword.py
│   └── service.py
│
├── vision/                  # screenshot, OCR, UI understand
├── memory/                  # SQLite + vector store + contacts
├── automation/              # Playwright, pyautogui wrappers
├── browser/                 # browser profiles / cookies (careful)
│
├── frontend/                # React HUD
│   └── public/              # voice console (available now)
├── electron/                # desktop shell + tray + hotkeys
│
├── plugins/                 # third-party skill packs
├── models/                  # local AI weights (gitignored)
├── database/                # jarvis.db, vectors
├── config/                  # user.yml examples
├── docs/
│   ├── architecture.md
│   ├── ROADMAP.md           # this file
│   ├── skills_guide.md
│   └── assets/              # logos, sample WAV
├── scripts/                 # run, validate, download-models
├── tests/
├── pyproject.toml
└── README.md
```

### Request flow (one command)

```
You: "Open YouTube and play lo-fi"
        │
        ▼
   Voice / Console / CLI
        │
        ▼
 POST /api/v1/skills/execute  (or /voice/command)
        │
        ▼
   Agent Orchestrator
   • parse intent + slots
   • build plan: [browser.open, media.search?]
   • check permissions
   • confirm if risky
        │
        ▼
   Skill Registry → skills.browser.open_url
        │
        ▼
   Sandbox / OS / Browser
        │
        ▼
   Result → TTS: "Opening YouTube, sir."
```

---

## 4. Build order (practical phases)

### Phase 0 — Done
- Core config + security  
- AI chat (Ollama + fallback)  
- Offline TTS + voice console  
- Memory stub  

### Phase 1 — One-command desktop ✅ DONE
1. Skill framework (`skills/base`, registry)  
2. Browser skill → open YouTube / any URL  
3. Apps skill → launch whitelisted apps  
4. Wire into `/voice/command` + console quick buttons  
5. Speak confirmation after action  

### Phase 2 — Email & accounts ✅ DONE (v2.1)
1. SMTP + Gmail compose skill  
2. Contacts memory (`data/contacts.json` + “add contact”)  
3. Confirm before SMTP send  
4. Draft mode default (safer)  
5. Guide: `docs/guides/email_and_voice.md`

### Phase 3 — Real JARVIS voice 🟡 PARTIAL
1. Piper adapter + download script ✅  
2. Deeper formant butler voice ✅  
3. Optional wake word 🔜  
4. Faster-whisper for always-local STT 🔜  

### Phase 4 — HUD + Electron
1. React Iron Man HUD  
2. Electron tray + global hotkey (Ctrl+Space)  
3. Waveform while listening/speaking  

### Phase 5 — Vision & automation
1. Screenshot + OCR  
2. Playwright “click the Login button”  
3. Multi-step agent plans  

### Phase 6 — Polish
1. Installer  
2. Plugin marketplace layout  
3. Tests + security audit  

---

## 5. Config you will need later

```env
# .env (never commit)
JARVIS_SECURITY_ALLOW_NETWORK=true          # only if you want email/web
JARVIS_EMAIL_SMTP_HOST=smtp.gmail.com
JARVIS_EMAIL_SMTP_USER=you@gmail.com
JARVIS_EMAIL_SMTP_PASSWORD=app-password
JARVIS_EMAIL_FROM=you@gmail.com

JARVIS_VOICE_TTS_ENGINE=piper               # formant | piper | xtts
JARVIS_VOICE_PIPER_MODEL=en_GB-alan-medium  # British male-ish

JARVIS_AI_DEFAULT_MODEL=llama3.2
```

---

## 6. Logo & branding

| Asset | Path | Use |
|-------|------|-----|
| Primary logo | `docs/assets/jarvis_logo.png` | README, about |
| Dark logo | `docs/assets/jarvis_logo_dark.png` | HUD, dark UI |
| Icon | `docs/assets/jarvis_icon.png` | Tray, favicon |
| Welcome WAV | `docs/assets/jarvis_welcome.wav` | Boot sound |

Style guide: cyan `#00E5FF`, gold `#C9A227`, void `#05080F`, arc-reactor geometry, HUD lines.

---

## 7. Voice upgrade path (honest)

| Priority | Action | Result |
|----------|--------|--------|
| 1 | Keep formant as fallback | Always works offline |
| 2 | Install **Piper** + British male model | Much more natural |
| 3 | Fine-tune speaking rate/pitch in settings | “Butler” cadence |
| 4 | Optional cloud TTS only when online | Movie-quality if allowed |
| 5 | Do **not** clone real actors without rights | Legal + ethics |

Movie Paul Bettany voice is copyrighted — we aim for a **similar character** (calm British butler AI), not a pirated clone.

---

## 8. Success criteria for “it works on one command”

- [ ] Say/type **“Open YouTube”** → browser opens in &lt; 2s + JARVIS speaks  
- [ ] **“Send email…”** → draft created; send only after confirm  
- [ ] **“Open VS Code”** → app launches  
- [ ] Every action in audit log  
- [ ] Denied actions explained by voice: “I need permission for that, sir.”  
- [ ] Works offline for local skills; network skills clearly marked  

---

## 9. What we’re implementing next in code

Immediate next drop (Phase 1 foundation):

1. `skills/` package + registry  
2. Browser + Apps skills  
3. Orchestrator hook in voice command  
4. Console buttons: YouTube, Gmail, Status  
5. Updated architecture diagram  

Then email skill when you provide SMTP / Gmail app password preference.

---

*“The suit and I are one.”* — structure first, then powers, then polish.
