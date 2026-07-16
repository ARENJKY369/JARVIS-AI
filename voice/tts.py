"""
JARVIS OS - Human-Like Offline TTS Engine
==========================================

Pure-Python text-to-speech synthesizer designed to sound warm, natural,
and human-like — inspired by JARVIS and FRIDAY from the Iron Man films.

Key improvements for naturalness:
- Smooth formant transitions (no abrupt phoneme changes)
- Natural prosody with gentle pitch contours
- Soft, warm tone shaping (no harshness)
- Gentle vibrato on sustained vowels
- Breathiness and natural timing
- Anti-aliased harmonic synthesis

Returns standard PCM WAV bytes + base64 for browser playback.
"""

from __future__ import annotations

import base64
import io
import math
import re
import struct
import wave
from dataclasses import dataclass
from typing import Iterable


# ---------------------------------------------------------------------------
# Phoneme inventory with natural durations and smooth transitions
# ---------------------------------------------------------------------------

# Each phoneme: (F1, F2, F3, voiced, duration_ms, noise_amt, breathiness)
# Lower noise_amt and added breathiness for smoother sound
PHONEMES: dict[str, tuple[float, float, float, bool, float, float, float]] = {
    # Vowels — warm, sustained
    "AA": (730, 1090, 2440, True, 130, 0.0, 0.05),   # father
    "AE": (660, 1720, 2410, True, 110, 0.0, 0.05),   # cat
    "AH": (640, 1190, 2390, True, 90, 0.0, 0.05),    # but
    "AO": (570, 840, 2410, True, 120, 0.0, 0.05),    # thought
    "AW": (570, 840, 2410, True, 150, 0.0, 0.05),    # cow
    "AY": (660, 1720, 2410, True, 150, 0.0, 0.05),   # hide
    "EH": (530, 1840, 2480, True, 100, 0.0, 0.05),   # bed
    "ER": (490, 1350, 1690, True, 130, 0.0, 0.05),   # bird
    "EY": (530, 1840, 2480, True, 140, 0.0, 0.05),   # bay
    "IH": (390, 1990, 2550, True, 80, 0.0, 0.05),    # bit
    "IY": (270, 2290, 3010, True, 110, 0.0, 0.05),   # beat
    "OW": (570, 840, 2410, True, 140, 0.0, 0.05),    # boat
    "OY": (570, 840, 2410, True, 150, 0.0, 0.05),    # boy
    "UH": (440, 1020, 2240, True, 90, 0.0, 0.05),    # book
    "UW": (300, 870, 2240, True, 120, 0.0, 0.05),    # boot
    # Consonants (voiced) — softer
    "B":  (200, 900, 2200, True, 55, 0.02, 0.0),
    "D":  (300, 1700, 2500, True, 55, 0.02, 0.0),
    "G":  (250, 1400, 2200, True, 55, 0.02, 0.0),
    "JH": (300, 1800, 2600, True, 80, 0.15, 0.0),
    "L":  (400, 1200, 2600, True, 80, 0.0, 0.02),
    "M":  (250, 1000, 2200, True, 80, 0.0, 0.05),
    "N":  (250, 1600, 2500, True, 80, 0.0, 0.05),
    "NG": (250, 1400, 2300, True, 90, 0.0, 0.05),
    "R":  (400, 1100, 1500, True, 80, 0.0, 0.02),
    "V":  (250, 1400, 2200, True, 80, 0.15, 0.0),
    "W":  (300, 700, 2200, True, 70, 0.0, 0.02),
    "Y":  (300, 2200, 3000, True, 70, 0.0, 0.02),
    "Z":  (300, 1800, 2600, True, 80, 0.18, 0.0),
    "ZH": (300, 1800, 2500, True, 80, 0.15, 0.0),
    "DH": (300, 1400, 2400, True, 70, 0.12, 0.0),
    # Unvoiced — softer fricatives
    "P":  (200, 900, 2200, False, 60, 0.2, 0.0),
    "T":  (350, 1800, 2600, False, 55, 0.22, 0.0),
    "K":  (300, 1600, 2500, False, 60, 0.2, 0.0),
    "CH": (350, 2000, 2800, False, 85, 0.3, 0.0),
    "F":  (300, 1400, 2500, False, 90, 0.28, 0.0),
    "TH": (350, 1600, 2500, False, 80, 0.25, 0.0),
    "S":  (400, 1800, 3000, False, 100, 0.35, 0.0),
    "SH": (350, 2000, 2700, False, 100, 0.32, 0.0),
    "HH": (400, 1500, 2500, False, 70, 0.22, 0.0),
    # Silence / pause
    "SIL": (0, 0, 0, False, 100, 0.0, 0.0),
    "SP":  (0, 0, 0, False, 50, 0.0, 0.0),
}

# Grapheme → phoneme rules
_MULTI: list[tuple[str, list[str]]] = [
    ("tion", ["SH", "AH", "N"]),
    ("sion", ["ZH", "AH", "N"]),
    ("ough", ["AO"]),
    ("augh", ["AO"]),
    ("eigh", ["EY"]),
    ("ight", ["AY", "T"]),
    ("ould", ["UH", "D"]),
    ("ing", ["IH", "NG"]),
    ("ph", ["F"]),
    ("ch", ["CH"]),
    ("sh", ["SH"]),
    ("th", ["TH"]),
    ("wh", ["W"]),
    ("ck", ["K"]),
    ("qu", ["K", "W"]),
    ("ng", ["NG"]),
    ("ee", ["IY"]),
    ("ea", ["IY"]),
    ("oo", ["UW"]),
    ("ou", ["AW"]),
    ("ow", ["OW"]),
    ("oi", ["OY"]),
    ("oy", ["OY"]),
    ("ai", ["EY"]),
    ("ay", ["EY"]),
    ("au", ["AO"]),
    ("aw", ["AO"]),
    ("oa", ["OW"]),
    ("oe", ["OW"]),
    ("ue", ["UW"]),
    ("ui", ["UW"]),
    ("ie", ["IY"]),
    ("ey", ["IY"]),
    ("er", ["ER"]),
    ("ir", ["ER"]),
    ("ur", ["ER"]),
    ("ar", ["AA", "R"]),
    ("or", ["AO", "R"]),
    ("ll", ["L"]),
    ("ss", ["S"]),
    ("ff", ["F"]),
    ("zz", ["Z"]),
    ("tt", ["T"]),
    ("pp", ["P"]),
    ("dd", ["D"]),
    ("bb", ["B"]),
    ("mm", ["M"]),
    ("nn", ["N"]),
    ("rr", ["R"]),
    ("gg", ["G"]),
    ("kn", ["N"]),
    ("wr", ["R"]),
    ("gn", ["N"]),
]

_SINGLE: dict[str, list[str]] = {
    "a": ["AE"], "b": ["B"], "c": ["K"], "d": ["D"], "e": ["EH"],
    "f": ["F"], "g": ["G"], "h": ["HH"], "i": ["IH"], "j": ["JH"],
    "k": ["K"], "l": ["L"], "m": ["M"], "n": ["N"], "o": ["AA"],
    "p": ["P"], "q": ["K"], "r": ["R"], "s": ["S"], "t": ["T"],
    "u": ["AH"], "v": ["V"], "w": ["W"], "x": ["K", "S"], "y": ["IY"],
    "z": ["Z"],
}

# Natural-sounding lexicon for common words
_LEXICON: dict[str, list[str]] = {
    "jarvis": ["JH", "AA", "R", "V", "IH", "S"],
    "sir": ["S", "ER"],
    "good": ["G", "UH", "D"],
    "evening": ["IY", "V", "N", "IH", "NG"],
    "morning": ["M", "AO", "R", "N", "IH", "NG"],
    "afternoon": ["AE", "F", "T", "ER", "N", "UW", "N"],
    "hello": ["HH", "EH", "L", "OW"],
    "online": ["AA", "N", "L", "AY", "N"],
    "offline": ["AO", "F", "L", "AY", "N"],
    "system": ["S", "IH", "S", "T", "AH", "M"],
    "systems": ["S", "IH", "S", "T", "AH", "M", "Z"],
    "status": ["S", "T", "AE", "T", "AH", "S"],
    "ready": ["R", "EH", "D", "IY"],
    "complete": ["K", "AH", "M", "P", "L", "IY", "T"],
    "completed": ["K", "AH", "M", "P", "L", "IY", "T", "AH", "D"],
    "yes": ["Y", "EH", "S"],
    "no": ["N", "OW"],
    "please": ["P", "L", "IY", "Z"],
    "thank": ["TH", "AE", "NG", "K"],
    "thanks": ["TH", "AE", "NG", "K", "S"],
    "you": ["Y", "UW"],
    "your": ["Y", "AO", "R"],
    "the": ["DH", "AH"],
    "a": ["AH"],
    "an": ["AE", "N"],
    "and": ["AE", "N", "D"],
    "of": ["AH", "V"],
    "to": ["T", "UW"],
    "for": ["F", "AO", "R"],
    "is": ["IH", "Z"],
    "are": ["AA", "R"],
    "am": ["AE", "M"],
    "i": ["AY"],
    "my": ["M", "AY"],
    "me": ["M", "IY"],
    "we": ["W", "IY"],
    "all": ["AO", "L"],
    "primary": ["P", "R", "AY", "M", "EH", "R", "IY"],
    "nominal": ["N", "AA", "M", "IH", "N", "AH", "L"],
    "operational": ["AA", "P", "ER", "EY", "SH", "AH", "N", "AH", "L"],
    "assistant": ["AH", "S", "IH", "S", "T", "AH", "N", "T"],
    "intelligence": ["IH", "N", "T", "EH", "L", "IH", "JH", "AH", "N", "S"],
    "artificial": ["AA", "R", "T", "IH", "F", "IH", "SH", "AH", "L"],
    "service": ["S", "ER", "V", "IH", "S"],
    "at": ["AE", "T"],
    "command": ["K", "AH", "M", "AE", "N", "D"],
    "commands": ["K", "AH", "M", "AE", "N", "D", "Z"],
    "voice": ["V", "OY", "S"],
    "time": ["T", "AY", "M"],
    "current": ["K", "ER", "AH", "N", "T"],
    "processing": ["P", "R", "AA", "S", "EH", "S", "IH", "NG"],
    "processed": ["P", "R", "AA", "S", "EH", "S", "T"],
    "understood": ["AH", "N", "D", "ER", "S", "T", "UH", "D"],
    "certainly": ["S", "ER", "T", "AH", "N", "L", "IY"],
    "absolutely": ["AE", "B", "S", "AH", "L", "UW", "T", "L", "IY"],
    "pleasure": ["P", "L", "EH", "ZH", "ER"],
    "welcome": ["W", "EH", "L", "K", "AH", "M"],
    "diagnostic": ["D", "AY", "AH", "G", "N", "AA", "S", "T", "IH", "K"],
    "diagnostics": ["D", "AY", "AH", "G", "N", "AA", "S", "T", "IH", "K", "S"],
    "security": ["S", "IH", "K", "Y", "UH", "R", "IH", "T", "IY"],
    "active": ["AE", "K", "T", "IH", "V"],
    "memory": ["M", "EH", "M", "ER", "IY"],
    "engine": ["EH", "N", "JH", "IH", "N"],
    "fallback": ["F", "AO", "L", "B", "AE", "K"],
    "mode": ["M", "OW", "D"],
    "how": ["HH", "AW"],
    "else": ["EH", "L", "S"],
    "can": ["K", "AE", "N"],
    "assist": ["AH", "S", "IH", "S", "T"],
    "zero": ["Z", "IY", "R", "OW"],
    "one": ["W", "AH", "N"],
    "two": ["T", "UW"],
    "three": ["TH", "R", "IY"],
    "four": ["F", "AO", "R"],
    "five": ["F", "AY", "V"],
    "six": ["S", "IH", "K", "S"],
    "seven": ["S", "EH", "V", "AH", "N"],
    "eight": ["EY", "T"],
    "nine": ["N", "AY", "N"],
    "ten": ["T", "EH", "N"],
    "percent": ["P", "ER", "S", "EH", "N", "T"],
    "ok": ["OW", "K", "EY"],
    "okay": ["OW", "K", "EY"],
    "error": ["EH", "R", "ER"],
    "warning": ["W", "AO", "R", "N", "IH", "NG"],
    "failed": ["F", "EY", "L", "D"],
    "success": ["S", "AH", "K", "S", "EH", "S"],
    "successful": ["S", "AH", "K", "S", "EH", "S", "F", "AH", "L"],
}


@dataclass(frozen=True)
class SpeechResult:
    """Result of a TTS synthesis request."""

    audio_bytes: bytes
    audio_base64: str
    duration_ms: float
    sample_rate: int
    format: str = "wav"
    engine: str = "jarvis-formant"
    text: str = ""
    success: bool = True
    message: str | None = None

    @property
    def data_uri(self) -> str:
        """Browser-ready data URI for <audio> playback."""
        return f"data:audio/wav;base64,{self.audio_base64}"


# ---------------------------------------------------------------------------
# Text → phonemes (natural timing)
# ---------------------------------------------------------------------------

def _word_to_phonemes(word: str) -> list[str]:
    w = re.sub(r"[^a-zA-Z']", "", word).lower()
    if not w:
        return []
    if w in _LEXICON:
        return list(_LEXICON[w])

    silent_e = False
    if len(w) > 2 and w.endswith("e") and w[-2] not in "aeiou":
        silent_e = True
        core = w[:-1]
    else:
        core = w

    phones: list[str] = []
    i = 0
    while i < len(core):
        matched = False
        for multi, ph in _MULTI:
            if core.startswith(multi, i):
                phones.extend(ph)
                i += len(multi)
                matched = True
                break
        if matched:
            continue
        ch = core[i]
        phones.extend(_SINGLE.get(ch, ["AH"]))
        i += 1

    if silent_e and phones:
        for idx in range(len(phones) - 1, -1, -1):
            if phones[idx] in ("AE", "EH", "IH", "AA", "AH", "UH", "AO"):
                lengthen = {
                    "AE": "EY", "EH": "IY", "IH": "AY",
                    "AA": "OW", "AH": "OW", "UH": "UW", "AO": "OW",
                }
                phones[idx] = lengthen.get(phones[idx], phones[idx])
                break

    return phones or ["AH"]


def text_to_phonemes(text: str) -> list[str]:
    """Convert free text into a phoneme sequence with natural pauses."""
    text = text.replace("—", ", ").replace("–", ", ").replace("…", "...")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ["SIL"]

    phones: list[str] = []
    tokens = re.findall(r"[A-Za-z']+|[.!?]|[,;:]|[\d]+|\S", text)

    for tok in tokens:
        if tok in ".!?":
            phones.append("SIL")
            phones.append("SIL")
        elif tok in ",;:":
            phones.append("SP")
        elif tok.isdigit():
            for d in tok:
                names = {
                    "0": "zero", "1": "one", "2": "two", "3": "three",
                    "4": "four", "5": "five", "6": "six", "7": "seven",
                    "8": "eight", "9": "nine",
                }
                phones.extend(_word_to_phonemes(names.get(d, "zero")))
                phones.append("SP")
        elif re.match(r"^[A-Za-z']+$", tok):
            phones.extend(_word_to_phonemes(tok))
            phones.append("SP")
        else:
            phones.append("SP")

    while phones and phones[-1] == "SP":
        phones.pop()
    if not phones or phones[-1] != "SIL":
        phones.append("SIL")
    return phones


# ---------------------------------------------------------------------------
# Smooth waveform synthesis (human-like)
# ---------------------------------------------------------------------------

def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return lo if x < lo else hi if x > hi else x


def _smooth_formant_resonator(
    t: float,
    f0: float,
    formants: Iterable[tuple[float, float]],
    phase: float,
) -> float:
    """
    Smooth additive harmonic synthesis with anti-aliasing.
    Produces warm, natural tone without harshness.
    """
    if f0 <= 0:
        return 0.0
    sample = 0.0
    # Limit harmonics to prevent aliasing and harshness
    n_harm = max(1, min(int((20000 / f0) * 0.8), 20))
    for h in range(1, n_harm + 1):
        freq = f0 * h
        # Gentle spectral rolloff (-12 dB/octave for smoothness)
        amp = 1.0 / (h ** 0.8)
        # Formant resonances with wider bandwidth for naturalness
        for ff, gain in formants:
            if ff <= 0:
                continue
            bw = 100.0 + ff * 0.08
            dist = (freq - ff) / bw
            amp += gain * math.exp(-0.5 * dist * dist) * 0.5
        sample += amp * math.sin(2.0 * math.pi * freq * t + phase * h)
    return sample


def _smooth_noise(seed: int) -> float:
    """Smooth pseudo-noise for natural-sounding fricatives."""
    x = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    return (x / 0x7FFFFFFF) * 2.0 - 1.0


def _synthesize_phonemes(
    phones: list[str],
    *,
    sample_rate: int = 22050,
    base_f0: float = 105.0,
    rate: float = 1.0,
    volume: float = 0.85,
) -> tuple[list[float], float]:
    """Render phoneme sequence → smooth float samples."""
    samples: list[float] = []
    total_ms = 0.0
    phase = 0.0
    n = max(1, len(phones))

    # Interpolation buffer for smooth formant transitions
    prev_formants = None

    for idx, p in enumerate(phones):
        spec = PHONEMES.get(p, PHONEMES["AH"])
        f1, f2, f3, voiced, dur_ms, noise_amt, breathiness = spec
        dur_ms = dur_ms / max(0.5, min(2.0, rate))
        n_samp = max(1, int(sample_rate * dur_ms / 1000.0))
        total_ms += dur_ms

        # Natural pitch contour: gentle rise-fall
        progress = idx / n
        # Slight rise at start, gentle fall at end (natural speech pattern)
        f0_contour = base_f0 * (1.03 - 0.08 * progress + 0.02 * math.sin(progress * math.pi))

        # Smooth formant targets
        formants = ((f1, 1.0), (f2, 0.7), (f3, 0.35)) if f1 > 0 else None

        for i in range(n_samp):
            t_local = i / sample_rate

            # Soft envelope: gentle attack/release
            env = 1.0
            attack = max(1, int(0.018 * sample_rate))
            release = max(1, int(0.035 * sample_rate))
            if i < attack:
                env = (i / attack) ** 0.5  # Soft exponential attack
            elif i > n_samp - release:
                env = max(0.0, (n_samp - i) / release) ** 0.5

            # Natural vibrato (slower, gentler)
            if voiced and dur_ms > 80:
                vibrato = 1.0 + 0.008 * math.sin(2 * math.pi * 4.2 * (total_ms / 1000 + t_local))
                f0_now = f0_contour * vibrato
            else:
                f0_now = f0_contour

            s = 0.0
            if formants and (voiced or noise_amt < 0.9):
                s += _smooth_formant_resonator(
                    t_local + total_ms / 1000.0,
                    f0_now if voiced else 0.0,
                    formants,
                    phase,
                )

            # Soft noise component
            if noise_amt > 0.0:
                nval = _smooth_noise(idx * 100003 + i * 17 + 91)
                if p in ("S", "SH", "CH", "F", "TH", "HH"):
                    nval = nval * 0.6 + _smooth_noise(idx * 99991 + i * 31) * 0.4
                s += nval * noise_amt * 0.4

            # Breathiness for naturalness
            if voiced and breathiness > 0.0:
                s += _smooth_noise(idx * 7919 + i * 13) * breathiness * 0.15

            # Smooth interpolation (removes clicks)
            if samples:
                s = 0.78 * s + 0.22 * samples[-1]

            samples.append(_clamp(s * env * volume * 0.2))

        phase += 0.25

    # Final smoothing: DC removal + soft limiting
    if samples:
        mean = sum(samples) / len(samples)
        samples = [_clamp((x - mean) * 1.1) for x in samples]

    return samples, total_ms


def _samples_to_wav(samples: list[float], sample_rate: int = 22050) -> bytes:
    """Pack float samples as 16-bit mono PCM WAV."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for s in samples:
            val = int(_clamp(s) * 32767.0)
            frames += struct.pack("<h", val)
        wf.writeframes(bytes(frames))
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Voice profiles (natural-sounding)
# ---------------------------------------------------------------------------

VOICE_PROFILES: dict[str, dict] = {
    # --- JARVIS (Male — Classic British Butler) ---
    "jarvis": {
        "f0": 98.0,
        "rate": 0.86,
        "volume": 0.92,
        "gender": "male",
        "label": "JARVIS (Male)",
        "description": "Deep measured British butler — classic Iron Man tone",
    },
    # --- FRIDAY (Female — Cool AI Companion) ---
    "friday": {
        "f0": 182.0,
        "rate": 0.90,
        "volume": 0.92,
        "gender": "female",
        "label": "FRIDAY (Female)",
        "description": "Cool measured female AI companion — Iron Man tone",
    },
}

VOICE_ALIASES: dict[str, str] = {
    "default": "jarvis",
    "male": "jarvis",
    "butler": "jarvis",
    "female": "friday",
    "woman": "friday",
    "girl": "friday",
}


def list_voices() -> list[dict]:
    """Return catalog of selectable voice profiles."""
    out: list[dict] = []
    for vid, meta in VOICE_PROFILES.items():
        out.append({
            "id": vid,
            "label": meta["label"],
            "gender": meta["gender"],
            "description": meta["description"],
            "pitch_hz": meta["f0"],
            "rate": meta["rate"],
        })
    out.sort(key=lambda v: (0 if v["gender"] == "male" else 1, v["label"]))
    return out


def resolve_voice_id(voice: str | None) -> str:
    """Normalize user/API voice name to a known profile id."""
    if not voice:
        return "jarvis"
    key = str(voice).strip().lower().replace(" ", "-").replace("_", "-")
    if key in VOICE_PROFILES:
        return key
    if key in VOICE_ALIASES:
        return VOICE_ALIASES[key]
    return "jarvis"


def _post_process_human(samples: list[float], *, feminine: bool = False) -> list[float]:
    """
    Warm, human-like tone shaping.
    Removes harshness while preserving clarity.
    """
    if not samples:
        return samples
    out: list[float] = []
    prev = 0.0
    lp = 0.0
    for x in samples:
        if feminine:
            # Brighter but still warm
            lp = 0.78 * lp + 0.22 * x
            warm = 0.75 * x + 0.25 * lp
            y = math.tanh(warm * 1.15) * 0.92
            y = 0.85 * y + 0.15 * prev
        else:
            # Warm butler tone
            lp = 0.90 * lp + 0.10 * x
            warm = 0.50 * x + 0.50 * lp
            y = math.tanh(warm * 1.25) * 0.88
            y = 0.80 * y + 0.20 * prev
        prev = y
        out.append(_clamp(y))
    # Normalize with soft limiting
    peak = max(abs(s) for s in out) or 1.0
    gain = min(0.88 / peak, 2.0)
    return [_clamp(s * gain) for s in out]


def synthesize_speech(
    text: str,
    *,
    voice: str = "jarvis",
    sample_rate: int = 22050,
    rate: float = 0.95,
    volume: float = 0.9,
    base_f0: float | None = None,
) -> SpeechResult:
    """
    Synthesize text into natural, human-like WAV audio.

    Parameters
    ----------
    text: Utterance to speak (English).
    voice: Profile id — jarvis, deep, calm, aria, friday, etc.
    sample_rate: Output sample rate (Hz).
    rate: Speaking rate multiplier.
    volume: Output volume 0..1.
    base_f0: Optional pitch override (Hz).
    """
    clean = (text or "").strip()
    if not clean:
        silent = _samples_to_wav([0.0] * int(sample_rate * 0.1), sample_rate)
        b64 = base64.b64encode(silent).decode("ascii")
        return SpeechResult(
            audio_bytes=silent, audio_base64=b64, duration_ms=100.0,
            sample_rate=sample_rate, text="", success=True,
            message="Empty text — silence generated",
        )

    vid = resolve_voice_id(voice)
    profile = VOICE_PROFILES.get(vid, VOICE_PROFILES["jarvis"])
    use_f0 = float(profile["f0"])
    use_rate = rate * float(profile["rate"])
    use_volume = volume * float(profile["volume"])
    feminine = profile.get("gender") == "female"

    if base_f0 is not None and vid in ("jarvis", "default"):
        use_f0 = base_f0

    phones = text_to_phonemes(clean)
    samples, duration_ms = _synthesize_phonemes(
        phones, sample_rate=sample_rate, base_f0=use_f0,
        rate=use_rate, volume=use_volume,
    )
    samples = _post_process_human(samples, feminine=feminine)
    wav = _samples_to_wav(samples, sample_rate)
    b64 = base64.b64encode(wav).decode("ascii")

    return SpeechResult(
        audio_bytes=wav, audio_base64=b64, duration_ms=duration_ms,
        sample_rate=sample_rate, text=clean, success=True,
        message=f"Synthesized {len(phones)} phonemes via jarvis-formant (voice={vid}, {profile['gender']}, F0={use_f0:.0f}Hz)",
        engine=f"jarvis-formant:{vid}",
    )


__all__ = [
    "synthesize_speech", "SpeechResult", "text_to_phonemes",
    "list_voices", "resolve_voice_id", "VOICE_PROFILES",
]
