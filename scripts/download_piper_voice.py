#!/usr/bin/env python3
"""
Download a Piper neural voice model for JARVIS-like British male speech.

Usage:
    python scripts/download_piper_voice.py
    python scripts/download_piper_voice.py --voice en_GB-alan-medium

Requires: pip install piper-tts  (and network once, to fetch the model)
Models are stored under models/piper/ and gitignored via models/.
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VOICE = "en_GB-alan-medium"

# HuggingFace rhasspy piper voices layout
HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


def voice_urls(voice: str) -> tuple[str, str, Path]:
    """
    Map voice id → (onnx_url, json_url, local_dir).
    en_GB-alan-medium → en/en_GB/alan/medium/
    """
    parts = voice.split("-")
    # en_GB-alan-medium
    if len(parts) < 3:
        raise SystemExit(f"Unexpected voice id: {voice}")
    locale = parts[0]  # en_GB
    name = parts[1]  # alan
    quality = parts[2]  # medium
    lang = locale.split("_")[0]  # en
    rel = f"{lang}/{locale}/{name}/{quality}/{voice}"
    onnx = f"{HF_BASE}/{rel}.onnx"
    meta = f"{HF_BASE}/{rel}.onnx.json"
    dest = ROOT / "models" / "piper" / voice
    return onnx, meta, dest


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  ↓ {url}")
    print(f"    → {dest}")
    urllib.request.urlretrieve(url, dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Piper voice for JARVIS")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Piper voice id")
    args = parser.parse_args()

    print("=" * 60)
    print("JARVIS OS — Piper voice downloader")
    print("=" * 60)
    print(f"Voice: {args.voice}")

    try:
        onnx_url, json_url, dest_dir = voice_urls(args.voice)
    except Exception as exc:
        print(f"Failed: {exc}")
        return 1

    onnx_path = dest_dir / f"{args.voice}.onnx"
    json_path = dest_dir / f"{args.voice}.onnx.json"

    if onnx_path.exists() and json_path.exists():
        print(f"Already present: {onnx_path}")
        print("Done.")
        return 0

    try:
        download(onnx_url, onnx_path)
        download(json_url, json_path)
    except Exception as exc:
        print(f"\nDownload failed: {exc}")
        print("You can still use the offline formant engine (no download needed).")
        print("Alternative: place any Piper .onnx under models/piper/")
        return 1

    print("\n✓ Voice installed.")
    print(f"  Model: {onnx_path}")
    print("  Set in .env (optional):")
    print(f"    JARVIS_VOICE_TTS_ENGINE=auto")
    print(f"    JARVIS_VOICE_TTS_MODEL={args.voice}")
    print("  Also: pip install piper-tts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
