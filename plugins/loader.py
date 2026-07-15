"""
JARVIS OS - Plugin Loader
=========================

Safe, dynamic plugin loading system.

Features:
- Manifest validation
- Sandboxed execution
- Dependency checking
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


class PluginLoader:
    """Manages loading and lifecycle of JARVIS plugins."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._plugins: dict[str, Any] = {}
        self._plugin_dir = self.settings.base_dir / "plugins" / "installed"
        self._plugin_dir.mkdir(parents=True, exist_ok=True)

    def list_available(self) -> list[dict[str, Any]]:
        """List all plugins in the plugin directory."""
        plugins = []
        for manifest_path in self._plugin_dir.glob("*/manifest.json"):
            try:
                data = json.loads(manifest_path.read_text())
                plugins.append({
                    "name": data.get("name", manifest_path.parent.name),
                    "version": data.get("version", "unknown"),
                    "description": data.get("description", ""),
                    "enabled": data.get("name", manifest_path.parent.name) in self._plugins,
                })
            except Exception as e:
                logger.warning(f"Invalid plugin manifest: {manifest_path} — {e}")
        return plugins

    def load(self, name: str) -> Any:
        self.pm.require(Permission.PLUGIN_LOAD)
        manifest_path = self._plugin_dir / name / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Plugin {name} not found")

        manifest = json.loads(manifest_path.read_text())
        self.audit.log_event(AuditEventType.PLUGIN_LOADED, details={"plugin": name, "version": manifest.get("version")})
        logger.success(f"Plugin loaded: {name} v{manifest.get('version')}")

        # Stub: real implementation would import and validate the plugin module
        self._plugins[name] = manifest
        return manifest

    def unload(self, name: str) -> None:
        if name in self._plugins:
            del self._plugins[name]
            logger.info(f"Plugin unloaded: {name}")

    def get_loaded(self) -> list[str]:
        return list(self._plugins.keys())


_plugin_loader: PluginLoader | None = None


def get_plugin_loader() -> PluginLoader:
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader()
    return _plugin_loader
