# JARVIS OS — Quality Standard (10/10)

**Policy:** Ship only when the quality gate scores **10/10 on every dimension**.

---

## How to run

```bash
cd JARVIS-AI
source .venv/bin/activate
export PYTHONPATH=.

# Full 10-dimension gate (must exit 0)
python scripts/quality_gate.py

# Unit tests
pytest tests/unit/ -o addopts= -q

# Legacy smoke validate
python scripts/validate.py
```

---

## The 10 dimensions

| # | Dimension | What “10” means |
|---|-----------|-----------------|
| 1 | Architecture & structure | All core modules, docs, scripts present |
| 2 | Core imports & configuration | Settings load, offline-first, voice/email config |
| 3 | Security model | Permissions, audit, sandbox, safe repr |
| 4 | Skills coverage | ≥20 skills, correct routing matrix |
| 5 | Voice & TTS | Real WAV, peak ≫ silence, formant engine |
| 6 | Personality & conversation | “sir”, empathy, system prompt |
| 7 | Orchestrator & missions | Skills + chat + multi-step planner |
| 8 | API surface | All critical GET/POST endpoints 200 |
| 9 | Automated unit tests | pytest exit 0, ≥50 tests |
| 10 | Docs, branding & DX | README, logo, guides, start script |

**Overall 10/10** = every dimension is perfect (no partial credit for the gate).

---

## Scorecard vs “Iron Man completeness”

| Concept | Meaning |
|---------|---------|
| **Quality 10/10** | Engineering excellence of *what is built* |
| **Iron Man OS ~60%** | Feature completeness vs the *movie fantasy* |

You can have **quality 10/10** on a **v1 product** without claiming full movie AGI.

---

## CI recommendation

```yaml
# example
- run: PYTHONPATH=. python scripts/quality_gate.py
- run: PYTHONPATH=. pytest tests/unit/ -o addopts= -q
```

Exit code **0** = green. Anything else = do not ship.
