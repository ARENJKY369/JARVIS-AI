# Email + Voice Setup Guide

## One-command email (works now)

### Safe mode (no password needed)

```
email test@example.com saying Hello from JARVIS
```

JARVIS will:
1. Parse **to / subject / body**
2. Save a draft under `data/email_drafts/`
3. Open **Gmail compose** in your browser with fields filled

### Contacts

Edit `data/contacts.json` or say:

```
add contact Mom email mom@gmail.com
```

Then:

```
email Mom saying I'll be late for dinner
```

### Real SMTP send (optional)

1. Copy `.env.example` → `.env`
2. For Gmail: Google Account → Security → 2FA → **App passwords**
3. Set:

```env
JARVIS_EMAIL_ENABLED=true
JARVIS_EMAIL_SMTP_USER=you@gmail.com
JARVIS_EMAIL_SMTP_PASSWORD=your-16-char-app-password
JARVIS_EMAIL_FROM=you@gmail.com
JARVIS_SECURITY_ALLOW_NETWORK=true
```

4. Command:

```
send email to alice@example.com saying Project is done
```

5. Confirm:

```
confirm send email
```

---

## JARVIS-like voice

### Default (always works)

Offline **formant butler voice** — deeper pitch, warmer tone, no downloads.

### Better neural voice (Piper)

```bash
source .venv/bin/activate
pip install piper-tts
python scripts/download_piper_voice.py
# restarts pick up model automatically (JARVIS_VOICE_TTS_ENGINE=auto)
```

British male default: `en_GB-alan-medium`

```env
JARVIS_VOICE_TTS_ENGINE=auto
JARVIS_VOICE_TTS_MODEL=en_GB-alan-medium
```

---

## Work with ChatGPT (one command)

```
ask chatgpt about machine learning
ask chatgpt how to write a resignation email
research climate change
explain recursion in python
help me write a cover letter for Google
summarize this: <paste long text>
open chatgpt
ask gemini about quantum physics
```

JARVIS will:
1. Give a short spoken answer (local brain / Ollama if running)
2. Open ChatGPT (or Gemini/Claude/Perplexity) with your question ready
3. Save the prompt under `data/work_prompts/`

---

## Console

http://127.0.0.1:8000/console

Quick buttons: Ask ChatGPT · Research · Write for me · YouTube · Gmail · Email · Search · Status
