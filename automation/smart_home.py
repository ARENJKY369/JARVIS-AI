"""
JARVIS OS - Smart Home / IoT Control
=====================================

Control smart home devices via common protocols:
- HTTP/REST APIs (Philips Hue, Tasmota, ESPHome, etc.)
- MQTT (generic IoT devices)
- Home Assistant integration
- Device discovery

Features:
- Light control (on/off, brightness, color)
- Switch/outlet control
- Sensor reading (temperature, humidity, motion)
- Scene activation
- Device discovery
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


class SmartDevice:
    """Represents a smart home device."""

    def __init__(self, device_id: str, name: str, device_type: str, protocol: str, address: str, room: str = ""):
        self.device_id = device_id
        self.name = name
        self.device_type = device_type  # light, switch, sensor, thermostat, camera
        self.protocol = protocol  # http, mqtt, homeassistant
        self.address = address
        self.room = room
        self.state: dict[str, Any] = {}
        self.online = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "type": self.device_type,
            "protocol": self.protocol,
            "address": self.address,
            "room": self.room,
            "state": self.state,
            "online": self.online,
        }


class SmartHomeController:
    """Smart home IoT controller supporting multiple protocols."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._devices: dict[str, SmartDevice] = {}
        self._mqtt_client = None
        self._load_devices()

    def _load_devices(self) -> None:
        """Load configured devices from data file."""
        path = self.settings.base_dir / self.settings.data_dir / "smart_home_devices.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                for dev in data.get("devices", []):
                    device = SmartDevice(
                        device_id=dev["device_id"],
                        name=dev["name"],
                        device_type=dev["type"],
                        protocol=dev.get("protocol", "http"),
                        address=dev["address"],
                        room=dev.get("room", ""),
                    )
                    self._devices[device.device_id] = device
                logger.info(f"Loaded {len(self._devices)} smart home devices")
            except Exception as e:
                logger.warning(f"Failed to load smart home devices: {e}")

    def _save_devices(self) -> None:
        """Save device configuration."""
        path = self.settings.base_dir / self.settings.data_dir / "smart_home_devices.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"devices": [d.to_dict() for d in self._devices.values()]}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_device(self, device_id: str, name: str, device_type: str, protocol: str, address: str, room: str = "") -> SmartDevice:
        """Add a new smart home device."""
        self.pm.require(Permission.AUTOMATION_EXECUTE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "add_device", "device_id": device_id})

        device = SmartDevice(device_id, name, device_type, protocol, address, room)
        self._devices[device_id] = device
        self._save_devices()
        logger.info(f"Added smart home device: {name} ({device_type})")
        return device

    def remove_device(self, device_id: str) -> bool:
        """Remove a smart home device."""
        self.pm.require(Permission.AUTOMATION_EXECUTE)
        if device_id in self._devices:
            del self._devices[device_id]
            self._save_devices()
            return True
        return False

    def list_devices(self, room: str | None = None, device_type: str | None = None) -> list[SmartDevice]:
        """List all devices, optionally filtered by room or type."""
        devices = list(self._devices.values())
        if room:
            devices = [d for d in devices if d.room.lower() == room.lower()]
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]
        return devices

    def get_device(self, name_or_id: str) -> SmartDevice | None:
        """Find a device by name or ID."""
        # Try exact ID first
        if name_or_id in self._devices:
            return self._devices[name_or_id]
        # Try by name (case-insensitive)
        for device in self._devices.values():
            if device.name.lower() == name_or_id.lower():
                return device
        # Try partial name match
        for device in self._devices.values():
            if name_or_id.lower() in device.name.lower():
                return device
        return None

    def control_light(self, device_name: str, action: str, **kwargs: Any) -> dict[str, Any]:
        """Control a light device."""
        self.pm.require(Permission.AUTOMATION_EXECUTE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "control_light", "device": device_name, "command": action})

        device = self.get_device(device_name)
        if not device:
            return {"success": False, "error": f"Light '{device_name}' not found"}

        if device.protocol == "http":
            return self._control_light_http(device, action, **kwargs)
        elif device.protocol == "homeassistant":
            return self._control_light_homeassistant(device, action, **kwargs)
        elif device.protocol == "mqtt":
            return self._control_light_mqtt(device, action, **kwargs)
        else:
            return {"success": False, "error": f"Unsupported protocol: {device.protocol}"}

    def _control_light_http(self, device: SmartDevice, action: str, **kwargs: Any) -> dict[str, Any]:
        """Control light via HTTP/REST API."""
        try:
            import urllib.request
            import urllib.parse

            if action == "on":
                payload = {"on": True}
            elif action == "off":
                payload = {"on": False}
            elif action == "toggle":
                payload = {"toggle": True}
            elif action == "brightness":
                payload = {"on": True, "bri": kwargs.get("brightness", 254)}
            elif action == "color":
                payload = {"on": True, "xy": kwargs.get("color_xy", [0.5, 0.5])}
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

            url = f"{device.address}/state"
            data = json.dumps(payload).encode()
            req = urllib.request.Request(url, data=data, method="PUT",
                                       headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read())
                device.state.update(payload)
                return {"success": True, "device": device.name, "action": action, "result": result}
        except Exception as e:
            logger.error(f"HTTP light control failed: {e}")
            return {"success": False, "error": str(e)}

    def _control_light_homeassistant(self, device: SmartDevice, action: str, **kwargs: Any) -> dict[str, Any]:
        """Control light via Home Assistant API."""
        try:
            import urllib.request

            service = f"light.turn_{action}"
            url = f"{device.address}/api/services/light/turn_{action}"
            payload = {"entity_id": device.device_id}
            if action == "on":
                if "brightness" in kwargs:
                    payload["brightness"] = kwargs["brightness"]
                if "color" in kwargs:
                    payload["rgb_color"] = kwargs["color"]

            data = json.dumps(payload).encode()
            token = kwargs.get("token", "")
            req = urllib.request.Request(url, data=data, method="POST",
                                       headers={
                                           "Content-Type": "application/json",
                                           "Authorization": f"Bearer {token}",
                                       })
            with urllib.request.urlopen(req, timeout=5) as resp:
                return {"success": True, "device": device.name, "action": action}
        except Exception as e:
            logger.error(f"Home Assistant light control failed: {e}")
            return {"success": False, "error": str(e)}

    def _control_light_mqtt(self, device: SmartDevice, action: str, **kwargs: Any) -> dict[str, Any]:
        """Control light via MQTT."""
        try:
            # MQTT control via publish
            topic = f"{device.address}/set"
            if action == "on":
                payload = '{"state":"ON"}'
            elif action == "off":
                payload = '{"state":"OFF"}'
            elif action == "brightness":
                payload = f'{{"state":"ON","brightness":{kwargs.get("brightness",254)}}}'
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

            self._mqtt_publish(topic, payload)
            return {"success": True, "device": device.name, "action": action}
        except Exception as e:
            logger.error(f"MQTT light control failed: {e}")
            return {"success": False, "error": str(e)}

    def control_switch(self, device_name: str, action: str) -> dict[str, Any]:
        """Control a smart switch/outlet."""
        self.pm.require(Permission.AUTOMATION_EXECUTE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "control_switch", "device": device_name, "command": action})

        device = self.get_device(device_name)
        if not device:
            return {"success": False, "error": f"Switch '{device_name}' not found"}

        try:
            if device.protocol == "mqtt":
                topic = f"{device.address}/set"
                payload = '{"state":"ON"}' if action == "on" else '{"state":"OFF"}'
                self._mqtt_publish(topic, payload)
                return {"success": True, "device": device.name, "action": action}
            elif device.protocol == "http":
                import urllib.request
                url = f"{device.address}/state"
                payload = {"on": action == "on"}
                data = json.dumps(payload).encode()
                req = urllib.request.Request(url, data=data, method="PUT",
                                           headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    return {"success": True, "device": device.name, "action": action}
            else:
                return {"success": False, "error": f"Unsupported protocol: {device.protocol}"}
        except Exception as e:
            logger.error(f"Switch control failed: {e}")
            return {"success": False, "error": str(e)}

    def read_sensor(self, device_name: str) -> dict[str, Any]:
        """Read a sensor value."""
        self.pm.require(Permission.SYSTEM_INFO)
        device = self.get_device(device_name)
        if not device:
            return {"success": False, "error": f"Sensor '{device_name}' not found"}

        try:
            if device.protocol == "http":
                import urllib.request
                with urllib.request.urlopen(device.address, timeout=5) as resp:
                    data = json.loads(resp.read())
                    device.state = data
                    return {"success": True, "device": device.name, "data": data}
            elif device.protocol == "mqtt":
                # MQTT sensors typically publish; return last known state
                return {"success": True, "device": device.name, "data": device.state}
            else:
                return {"success": False, "error": f"Unsupported protocol: {device.protocol}"}
        except Exception as e:
            logger.error(f"Sensor read failed: {e}")
            return {"success": False, "error": str(e)}

    def activate_scene(self, scene_name: str) -> dict[str, Any]:
        """Activate a predefined scene."""
        self.pm.require(Permission.AUTOMATION_EXECUTE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "activate_scene", "scene": scene_name})

        # Load scenes
        path = self.settings.base_dir / self.settings.data_dir / "smart_home_scenes.json"
        if not path.exists():
            return {"success": False, "error": "No scenes configured"}

        try:
            scenes = json.loads(path.read_text())
            if scene_name not in scenes:
                return {"success": False, "error": f"Scene '{scene_name}' not found"}

            scene = scenes[scene_name]
            results = []
            for action in scene.get("actions", []):
                device = self.get_device(action["device"])
                if device:
                    if device.device_type == "light":
                        result = self.control_light(action["device"], action["action"], **action.get("params", {}))
                    elif device.device_type == "switch":
                        result = self.control_switch(action["device"], action["action"])
                    else:
                        result = {"success": False, "error": "Unknown device type"}
                    results.append(result)

            return {"success": True, "scene": scene_name, "results": results}
        except Exception as e:
            logger.error(f"Scene activation failed: {e}")
            return {"success": False, "error": str(e)}

    def _mqtt_publish(self, topic: str, payload: str) -> None:
        """Publish an MQTT message."""
        try:
            import paho.mqtt.client as mqtt
            client = mqtt.Client()
            client.connect(self.settings.base_dir / "mqtt_broker" / "address", 1883, 60)
            client.publish(topic, payload)
            client.disconnect()
        except ImportError:
            logger.warning("paho-mqtt not installed — MQTT unavailable")
            raise
        except Exception as e:
            logger.error(f"MQTT publish failed: {e}")
            raise

    def get_status(self) -> dict[str, Any]:
        """Get overall smart home status."""
        return {
            "total_devices": len(self._devices),
            "lights": len([d for d in self._devices.values() if d.device_type == "light"]),
            "switches": len([d for d in self._devices.values() if d.device_type == "switch"]),
            "sensors": len([d for d in self._devices.values() if d.device_type == "sensor"]),
            "thermostats": len([d for d in self._devices.values() if d.device_type == "thermostat"]),
            "rooms": list(set(d.room for d in self._devices.values() if d.room)),
            "devices": [d.to_dict() for d in self._devices.values()],
        }


_smart_home: SmartHomeController | None = None


def get_smart_home() -> SmartHomeController:
    global _smart_home
    if _smart_home is None:
        _smart_home = SmartHomeController()
    return _smart_home
