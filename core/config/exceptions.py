"""
JARVIS OS - Configuration Exceptions
====================================

Domain-specific exceptions for the configuration system.

These provide clear, actionable errors to developers and operators.
"""

from __future__ import annotations


class ConfigError(Exception):
    """Base exception for all configuration-related failures."""

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class InvalidEnvironmentError(ConfigError):
    """Raised when an unsupported environment is requested."""

    pass


class MissingRequiredConfigError(ConfigError):
    """Raised when a required configuration value is missing or invalid."""

    pass


class PathSecurityError(ConfigError):
    """Raised when a configuration path violates security policies (traversal etc.)."""

    pass


class DirectoryCreationError(ConfigError):
    """Raised when required directories cannot be created."""

    pass
