"""
JARVIS OS - Core Configuration (settings.py)
============================================

Production-grade, immutable, type-safe configuration using Pydantic v2.

This module is the single source of truth for all runtime configuration.

Key Properties:
- Fully validated at startup
- Environment variable driven with JARVIS_ prefix
- .env file support (never committed)
- Sensible offline-first defaults
- Paths are always resolved to absolute
- Secrets are never logged or exposed in repr
- Supports multiple environments: development, production, testing

Architecture Decision:
- Uses BaseSettings from pydantic-settings (recommended pattern)
- Singleton via get_settings() with lru_cache for performance
- Explicit model_config for strict validation
- Custom validators for directory creation and path safety
- Frozen model (immutable after creation)

Security Model:
- No secrets stored in model fields that are sensitive by default
- Path fields are validated against traversal attacks
- Environment variables override everything
- .env is git-ignored

Usage (recommended):
    from core.config import get_settings

    settings = get_settings()
    db_path = settings.database.path

Direct instantiation is discouraged outside of tests.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import ConfigError  # type: ignore


class DatabaseConfig(BaseSettings):
    """Database configuration block."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    engine: Literal["sqlite", "chromadb"] = Field(
        default="sqlite",
        description="Primary storage engine. sqlite for relational + metadata. chromadb for vector.",
    )
    path: Path = Field(
        default=Path("database/jarvis.db"),
        description="Path to the primary SQLite database file (relative to project root).",
    )
    vector_path: Path = Field(
        default=Path("database/vector_store"),
        description="Directory for vector database (Chroma or LanceDB).",
    )
    echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy echo (debug only).",
    )

    @field_validator("path", "vector_path", mode="before")
    @classmethod
    def _resolve_path(cls, v: str | Path) -> Path:
        raw = str(v)
        if ".." in raw:
            raise ValueError("Path traversal not allowed in database paths")
        path = Path(v).expanduser().resolve()
        # Final safety: ensure resolved path does not contain .. segments
        if any(part == ".." for part in path.parts):
            raise ValueError("Path traversal not allowed in database paths")
        return path


class AIConfig(BaseSettings):
    """Local AI / LLM configuration (Ollama by default)."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_AI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: Literal["ollama", "local"] = Field(
        default="ollama",
        description="LLM provider. Only 'ollama' supported in v1.0 for offline-first.",
    )
    ollama_host: str = Field(
        default="http://127.0.0.1:11434",
        description="Ollama server URL. Must be localhost for offline mode.",
    )
    default_model: str = Field(
        default="llama3.2",
        description="Default model to use for general reasoning. Must be pulled locally.",
    )
    vision_model: str = Field(
        default="llava",
        description="Vision-capable model (for multimodal).",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for generation.",
    )
    max_tokens: int = Field(
        default=2048,
        ge=128,
        le=32768,
        description="Maximum tokens for model output.",
    )
    context_window: int = Field(
        default=8192,
        description="Context length to request from Ollama.",
    )
    timeout: int = Field(
        default=120,
        ge=10,
        description="Request timeout in seconds.",
    )

    @field_validator("ollama_host")
    @classmethod
    def _validate_ollama_host(cls, v: str) -> str:
        if not (v.startswith("http://127.0.0.1") or v.startswith("http://localhost")):
            raise ValueError(
                "For security and offline-first compliance, ollama_host must be localhost"
            )
        return v


class VoiceConfig(BaseSettings):
    """Voice (STT + TTS) configuration."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_VOICE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(default=True)
    stt_model: str = Field(
        default="base",
        description="faster-whisper model size (tiny, base, small, medium, large).",
    )
    tts_engine: Literal["formant", "piper", "auto"] = Field(
        default="auto",
        description="TTS backend: formant (always), piper (if installed), auto (prefer piper).",
    )
    tts_model: str = Field(
        default="en_GB-alan-medium",
        description="Piper voice model name (British male recommended for JARVIS).",
    )
    piper_model_path: Path | None = Field(
        default=None,
        description="Optional absolute path to a Piper .onnx model file.",
    )
    sample_rate: int = Field(default=22050, ge=8000, le=48000)
    language: str = Field(default="en")
    device: Literal["cpu", "cuda"] = Field(default="cpu")
    energy_threshold: float = Field(
        default=0.02,
        ge=0.001,
        le=1.0,
        description="VAD energy threshold for voice activity detection.",
    )
    speaking_rate: float = Field(default=0.92, ge=0.5, le=2.0)
    pitch_hz: float = Field(
        default=98.0,
        ge=70.0,
        le=200.0,
        description="Base F0 for formant JARVIS voice (lower = deeper butler tone).",
    )


class VisionConfig(BaseSettings):
    """Computer vision and OCR configuration."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_VISION_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(default=True)
    ocr_engine: Literal["tesseract", "easyocr"] = Field(default="tesseract")
    screenshot_quality: int = Field(default=85, ge=50, le=100)
    max_image_size: int = Field(
        default=1920, description="Max width/height for processing."
    )


class SecurityConfig(BaseSettings):
    """Security, sandbox and permission settings."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sandbox_enabled: bool = Field(
        default=True,
        description="Enable execution sandbox for automation and code execution.",
    )
    allow_network: bool = Field(
        default=False, description="Allow any network calls (disabled in offline mode)."
    )
    allowed_commands: list[str] = Field(
        default_factory=lambda: ["ls", "cat", "echo", "python"],
        description="Whitelist of shell commands that can be executed via automation.",
    )
    max_execution_time: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Maximum seconds any automation action can run.",
    )
    audit_log: bool = Field(default=True)


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    file_enabled: bool = Field(default=True)
    max_file_size_mb: int = Field(default=50, ge=5)
    backup_count: int = Field(default=5)
    json_format: bool = Field(default=False, description="Use structured JSON logs.")


class UIConfig(BaseSettings):
    """Frontend / Electron UI preferences."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_UI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    theme: Literal["dark", "light", "system"] = Field(default="dark")
    show_console: bool = Field(default=False)
    animation_speed: float = Field(default=1.0, ge=0.1, le=3.0)
    default_voice: str = Field(default="jarvis")
    user_name: str = Field(
        default="", description="Display name for the operator (e.g. Tony)."
    )
    user_avatar: str = Field(
        default="",
        description="Path or URL to the operator's profile picture (optional).",
    )


class EmailConfig(BaseSettings):
    """SMTP email configuration for the email skill."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_EMAIL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    enabled: bool = Field(
        default=False,
        description="Master switch for SMTP sending (drafts always work).",
    )
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="", description="SMTP password or app password (never logged).")
    from_address: str = Field(default="")
    use_tls: bool = Field(default=True)
    # Safety: never send without explicit confirmation unless this is True
    require_confirmation: bool = Field(default=True)
    # Default mode when user says "send email" without confirm
    default_mode: Literal["draft", "send"] = Field(default="draft")

    def is_configured(self) -> bool:
        return bool(self.enabled and self.smtp_host and self.smtp_user and self.smtp_password)

    def __repr__(self) -> str:
        return (
            f"<EmailConfig(enabled={self.enabled}, host={self.smtp_host!r}, "
            f"user={'***' if self.smtp_user else ''!r}, configured={self.is_configured()})>"
        )


class Settings(BaseSettings):
    """
    Root JARVIS OS Configuration.

    This is the single authoritative configuration object.
    All fields are validated and frozen.
    """

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
        frozen=True,
    )

    # Top level
    app_name: str = Field(default="JARVIS OS", frozen=True)
    version: str = Field(default="1.0.0")
    environment: Literal["development", "production", "testing"] = Field(
        default="development"
    )
    debug: bool = Field(default=False)

    # Paths (resolved relative to project root)
    base_dir: Path = Field(
        default=Path(__file__).parent.parent.parent.resolve(),
        description="Absolute path to the JARVIS OS project root.",
    )
    data_dir: Path = Field(default=Path("data"))
    logs_dir: Path = Field(default=Path("logs"))
    models_dir: Path = Field(default=Path("models"))
    temp_dir: Path = Field(default=Path("temp"))

    # Sub-configs (nested)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)

    @model_validator(mode="after")
    def _ensure_directories(self) -> Settings:
        """Create required directories on first load (idempotent)."""
        dirs_to_create = [
            self.base_dir / self.data_dir,
            self.base_dir / self.logs_dir,
            self.base_dir / self.models_dir,
            self.base_dir / self.temp_dir,
            self.base_dir / self.database.path.parent,
            self.base_dir / self.database.vector_path,
        ]
        for directory in dirs_to_create:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise ConfigError(
                    f"Failed to create required directory {directory}: {exc}"
                ) from exc
        return self

    @field_validator("base_dir", mode="before")
    @classmethod
    def _resolve_base_dir(cls, v: str | Path | None) -> Path:
        if v is None:
            return Path(__file__).parent.parent.parent.resolve()
        return Path(v).expanduser().resolve()

    @field_validator("environment")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        if v not in ("development", "production", "testing"):
            raise ValueError("Invalid environment")
        return v

    @field_validator("debug")
    @classmethod
    def _validate_debug_in_prod(cls, v: bool, info: dict) -> bool:
        # Access via info.data in Pydantic v2
        env = info.data.get("environment", "development")
        if env == "production" and v:
            raise ValueError("Debug mode must be False in production")
        return v

    def get_database_path(self) -> Path:
        """Return absolute database path."""
        return (self.base_dir / self.database.path).resolve()

    def get_vector_db_path(self) -> Path:
        """Return absolute vector database directory."""
        return (self.base_dir / self.database.vector_path).resolve()

    def is_production(self) -> bool:
        return self.environment == "production"

    def is_offline_mode(self) -> bool:
        """True when network features are disabled (default)."""
        return not self.security.allow_network

    def __repr__(self) -> str:
        """Safe repr that hides sensitive information."""
        return (
            f"<Settings(app_name={self.app_name!r}, version={self.version!r}, "
            f"env={self.environment!r}, debug={self.debug})>"
        )


# =============================================================================
# Singleton Accessor + Exceptions
# =============================================================================


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached, validated Settings instance.

    This is the recommended way to access configuration anywhere in the system.
    The cache is cleared only on process restart (or manually via _clear_cache).

    In tests, you can override using Settings.model_validate or monkeypatch.
    """
    try:
        return Settings()
    except Exception as exc:
        # Convert pydantic validation errors to our domain error
        raise ConfigError(f"Configuration validation failed: {exc}") from exc


def _clear_settings_cache() -> None:
    """Test utility only. Clears the settings cache."""
    get_settings.cache_clear()


# =============================================================================
# Convenience Exports
# =============================================================================

__all__ = [
    "Settings",
    "get_settings",
    "ConfigError",
    "_clear_settings_cache",
    "DatabaseConfig",
    "AIConfig",
    "VoiceConfig",
    "VisionConfig",
    "SecurityConfig",
    "LoggingConfig",
    "UIConfig",
    "EmailConfig",
]
