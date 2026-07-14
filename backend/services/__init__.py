"""
JARVIS OS - Backend Services Layer
==================================

Services contain the core business logic.

All services are:
- Stateless where possible
- Depend on core primitives (config, security, memory)
- Fully type-hinted
- Async-friendly
"""

from .ai_service import AIService, get_ai_service

__all__ = ["AIService", "get_ai_service"]
