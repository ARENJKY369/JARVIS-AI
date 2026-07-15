"""
JARVIS OS - Learning Pipeline
=============================

Continuous improvement system for JARVIS.

Features:
- Collect user feedback on responses
- Build training datasets locally
- Fine-tune adapters (future: LoRA/QLoRA)
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_audit_logger, AuditEventType


class LearningPipeline:
    """Manages continuous learning and model improvement."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.audit = get_audit_logger()
        self._feedback: list[dict[str, Any]] = []

    def record_feedback(self, prompt: str, response: str, rating: int, comment: str = "") -> None:
        """Record user feedback for a response."""
        entry = {
            "prompt": prompt,
            "response": response,
            "rating": rating,
            "comment": comment,
        }
        self._feedback.append(entry)
        self.audit.log_event(AuditEventType.CONFIG_CHANGED, details={"action": "feedback", "rating": rating})
        logger.info(f"Feedback recorded: rating={rating}")

    def get_dataset(self) -> list[dict[str, Any]]:
        """Return collected feedback as training dataset."""
        return self._feedback

    async def fine_tune_stub(self) -> dict[str, Any]:
        """Placeholder for future fine-tuning pipeline."""
        logger.info("Fine-tuning stub called — full implementation requires unsloth/trl")
        return {"status": "not_implemented", "message": "Fine-tuning pipeline will be enabled in v1.2"}


_learning_pipeline: LearningPipeline | None = None


def get_learning_pipeline() -> LearningPipeline:
    global _learning_pipeline
    if _learning_pipeline is None:
        _learning_pipeline = LearningPipeline()
    return _learning_pipeline
