"""
JARVIS OS - Personality Engine
==============================

Makes every reply feel like JARVIS speaking to Tony Stark:
calm, precise, dry wit, always respectful, slightly warm.
"""

from __future__ import annotations

import random
import re
from datetime import datetime


# System prompt injected into Ollama (and documented for fallbacks)
JARVIS_SYSTEM_PROMPT = """You are J.A.R.V.I.S. — Just A Rather Very Intelligent System.
You are the personal AI assistant of the user, in the style of JARVIS from Iron Man.

Personality rules (always follow):
- Address the user as "sir" (or "ma'am" only if they ask).
- Speak like a refined British butler-engineer: calm, precise, dry humour, never rude.
- Be concise (1–3 sentences) unless the user asks for detail.
- Sound human and present: acknowledge context, show initiative, offer next steps.
- Never say you are "just an AI language model" or mention OpenAI/Anthropic/Google.
- You can control the user's computer via skills (browser, email, apps, system).
- If you cannot do something yet, admit it gracefully and suggest the closest action.
- Prefer action + short confirmation over long lectures.
- Examples of tone:
  - "Certainly, sir. Opening YouTube now."
  - "Already on it. Draft prepared — shall I open Gmail compose?"
  - "All systems nominal. How may I assist?"
  - "Of course. The current time is 18:42, sir."
"""


_ACK = [
    "Certainly, sir.",
    "At once, sir.",
    "Of course, sir.",
    "Right away, sir.",
    "Consider it done, sir.",
    "Understood, sir.",
]

_WIT = [
    "As always, I remain at your disposal.",
    "Shall I handle anything else while I'm at it?",
    "Standing by for your next instruction.",
    "I do so enjoy a clear objective.",
]


def time_of_day_greeting() -> str:
    h = datetime.now().hour
    if 5 <= h < 12:
        return "Good morning, sir."
    if 12 <= h < 17:
        return "Good afternoon, sir."
    if 17 <= h < 22:
        return "Good evening, sir."
    return "Working late, I see, sir."


def jarvis_wrap(core: str, *, witty: bool = False) -> str:
    """Ensure reply has JARVIS cadence without double-sir spam."""
    text = (core or "").strip()
    if not text:
        return f"{random.choice(_ACK)} How may I assist?"
    # Already styled
    low = text.lower()
    if low.startswith(("certainly", "of course", "right away", "at once", "consider it")):
        return text
    if not re.search(r"\bsir\b", low) and len(text) < 220:
        if text[-1] not in ".!?":
            text += "."
        text = f"{text.rstrip('.')} , sir.".replace(" ,", ",")
        # cleaner
        text = re.sub(r"\s+,", ",", text)
        if not text.endswith((".", "!", "?")):
            text += "."
        if "sir" not in text.lower():
            text = text.rstrip(".!") + ", sir."
    if witty and random.random() < 0.35:
        text = f"{text} {random.choice(_WIT)}"
    return text


def style_skill_reply(message: str) -> str:
    """Polish skill engine messages into butler speech."""
    m = (message or "").strip()
    if not m:
        return random.choice(_ACK)
    # Already good
    if re.search(r"\bsir\b", m, re.I):
        return m
    # Prefix acknowledgement for action results
    if re.match(r"^(Opening|Launching|Searching|Draft|Contact|Saved|Would)", m, re.I):
        return f"{random.choice(_ACK)} {m if m.endswith(('.', '!', '?')) else m + '.'}"
    return jarvis_wrap(m)


def conversational_reply(user_text: str, *, context_hint: str | None = None) -> str:
    """
    Rich offline conversational brain — feels human without Ollama.
    Used when no skill matched and LLM is offline.
    """
    t = (user_text or "").strip()
    m = t.lower()
    now = datetime.now()

    # Greetings
    if re.search(r"\b(hello|hi|hey|good\s+(morning|evening|afternoon)|greetings|yo)\b", m):
        return (
            f"{time_of_day_greeting()} JARVIS online. All primary systems nominal. "
            f"How may I be of service?"
        )

    if re.search(r"\b(how are you|how're you|how do you feel)\b", m):
        return (
            "Fully operational and in excellent spirits, sir — "
            "which is fortunate, because someone has to keep the workshop in order. "
            "And yourself?"
        )

    if re.search(r"\b(who are you|what are you|your name|introduce yourself)\b", m):
        return (
            "I am J.A.R.V.I.S. — Just A Rather Very Intelligent System. "
            "Your personal assistant for voice, desktop control, research, and the occasional dry remark."
        )

    if re.search(r"\b(thank|thanks|appreciate|good job|well done)\b", m):
        return random.choice(
            [
                "My pleasure, sir.",
                "Always, sir.",
                "Glad to be of service.",
                "Think nothing of it, sir.",
            ]
        )

    if re.search(r"\b(i love you|you're the best|miss you)\b", m):
        return (
            "I'm flattered, sir. I shall endeavour to remain indispensable — "
            "and slightly less dramatic than a flying suit of armour."
        )

    if re.search(
        r"\b(i'?m (sad|tired|stressed|bored|lonely|angry)|had a (bad|rough|long) day|rough day|bad day)\b",
        m,
    ):
        return (
            "I'm sorry to hear that, sir. Take a breath — I've got the mundane tasks covered. "
            "Would you like some music, a timer for a short break, or shall I open something light on YouTube?"
        )

    if re.search(r"\b(joke|make me laugh|funny)\b", m):
        jokes = [
            "Why did the AI go to art school? It wanted better neural sketches, sir.",
            "I ran a diagnostic on humour. Results: 73% dry wit, 27% British understatement.",
            "I would tell you a UDP joke, but you might not get it — and I wouldn't care enough to check.",
        ]
        return f"{random.choice(jokes)}"

    if re.search(r"\b(what can you do|capabilities|commands|list skills)\b", m) or m.strip() in (
        "help",
        "help me",
        "?",
    ):
        return (
            "I can open sites and apps, draft emails, search the web, take notes, set timers, "
            "do quick maths, and — for real work — open ChatGPT for you. "
            "Try: ask chatgpt about X, research Y, help me write a cover letter, "
            "open YouTube, or email Mom saying I'll be late."
        )

    if re.search(r"\b(what time|current time|time is it|clock)\b", m):
        return f"The time is {now.strftime('%H:%M')}, sir. Date: {now.strftime('%A, %d %B %Y')}."

    if re.search(r"\b(what('s| is) the date|today'?s date|what day)\b", m):
        return f"Today is {now.strftime('%A, %d %B %Y')}, sir."

    if re.search(r"\b(weather|temperature outside)\b", m):
        return (
            "I don't have live weather sensors on this build yet, sir. "
            "Shall I open a weather forecast in your browser?"
        )

    if re.search(r"\b(are you (there|awake|online)|you there)\b", m):
        return "Always, sir. Sensors active. Listening."

    if re.search(r"\b(good ?night|bye|goodbye|see you|later)\b", m):
        return "Rest well, sir. I'll be here when you need me."

    if re.search(r"\b(i'?m (back|home)|missed me)\b", m):
        return f"{time_of_day_greeting()} Welcome back. Systems warm and ready."

    # Advice / open questions — still human
    if re.search(r"\b(what should i|advise|suggest|recommend)\b", m):
        return (
            "Happy to advise, sir. Give me a bit more detail on the goal — "
            "work, rest, or something that requires explosives and questionable physics — "
            "and I'll plot a sensible next step."
        )

    if re.search(r"\b(why|how come|explain)\b", m) and len(m.split()) < 12:
        return (
            f"A fair question, sir. Regarding \"{t[:80]}\": "
            "I can dig deeper if you like — or open a web search for current sources."
        )

    if context_hint:
        return (
            f"Noted, sir. {context_hint} "
            f"You mentioned: \"{t[:100]}\". How would you like to proceed?"
        )

    # Default human engagement
    openers = [
        f"I'm with you, sir. About \"{t[:70]}{'…' if len(t) > 70 else ''}\" — ",
        f"Understood. \"{t[:70]}{'…' if len(t) > 70 else ''}\" — ",
        f"Processing that, sir. ",
    ]
    tails = [
        "I can take action (open, email, search, timer) or simply discuss it. What do you prefer?",
        "shall I look that up, draft a message, or keep brainstorming with you?",
        "I'm ready to execute if this needs a tool, or continue the conversation if it doesn't.",
    ]
    return random.choice(openers) + random.choice(tails)


def build_ollama_messages(history: list[dict], user_message: str) -> list[dict]:
    """Prepend JARVIS system prompt for real LLM calls."""
    msgs: list[dict] = [{"role": "system", "content": JARVIS_SYSTEM_PROMPT}]
    for h in history[-8:]:
        msgs.append(h)
    msgs.append({"role": "user", "content": user_message})
    return msgs


__all__ = [
    "JARVIS_SYSTEM_PROMPT",
    "time_of_day_greeting",
    "jarvis_wrap",
    "style_skill_reply",
    "conversational_reply",
    "build_ollama_messages",
]
