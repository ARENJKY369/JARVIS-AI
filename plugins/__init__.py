"""
JARVIS OS - Plugin System
=========================

Dynamic plugin loader and registry.

Features:
- Hot-reloadable plugins
- Sandboxed plugin execution
- Plugin manifest validation
"""

from .loader import PluginLoader, get_plugin_loader

__all__ = ["PluginLoader", "get_plugin_loader"]
