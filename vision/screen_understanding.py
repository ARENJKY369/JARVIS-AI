"""
JARVIS OS - Screen Understanding (OCR + UI Tree)
=================================================

Advanced screen understanding combining OCR with UI element detection.

Features:
- Full screen OCR with layout preservation
- UI element detection (buttons, text fields, menus)
- Clickable element mapping
- Screen region analysis
- Text localization
- UI tree extraction (accessibility)
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


@dataclass
class UIElement:
    """Represents a UI element on screen."""
    element_type: str  # button, text_field, checkbox, menu, link, image, label
    text: str
    x: int
    y: int
    width: int
    height: int
    clickable: bool = False
    enabled: bool = True
    confidence: float = 0.0
    children: list["UIElement"] = field(default_factory=list)

    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.element_type,
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "clickable": self.clickable,
            "enabled": self.enabled,
            "confidence": self.confidence,
            "children": [c.to_dict() for c in self.children],
        }


class ScreenUnderstanding:
    """Screen understanding with OCR and UI tree extraction."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._ocr_engine = None
        self._ui_detector = None

    def capture_and_analyze(self) -> dict[str, Any]:
        """Capture screen and perform full analysis."""
        self.pm.require(Permission.VISION_CAPTURE)
        self.pm.require(Permission.VISION_ANALYZE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "screen_analyze"})

        screenshot_path = self._capture_screenshot()
        if not screenshot_path:
            return {"success": False, "error": "Screenshot failed"}

        # OCR analysis
        ocr_text = self._run_ocr(screenshot_path)
        text_regions = self._extract_text_regions(screenshot_path)

        # UI element detection
        ui_elements = self._detect_ui_elements(screenshot_path)

        return {
            "success": True,
            "screenshot": screenshot_path,
            "text": ocr_text,
            "text_regions": text_regions,
            "ui_elements": [e.to_dict() for e in ui_elements],
            "element_count": len(ui_elements),
            "clickable_count": len([e for e in ui_elements if e.clickable]),
        }

    def _capture_screenshot(self) -> str | None:
        """Capture a screenshot."""
        try:
            import pyautogui
            path = self.settings.base_dir / "temp" / f"screen_{int(time.time())}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            pyautogui.screenshot(str(path))
            return str(path)
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    def _run_ocr(self, image_path: str) -> str:
        """Run OCR on an image."""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            return pytesseract.image_to_string(img).strip()
        except ImportError:
            return "[OCR unavailable — install pytesseract]"
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return f"[OCR error: {e}]"

    def _extract_text_regions(self, image_path: str) -> list[dict[str, Any]]:
        """Extract text regions with bounding boxes."""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            regions = []
            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                if text:
                    regions.append({
                        "text": text,
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i],
                        "confidence": data["conf"][i],
                    })
            return regions
        except ImportError:
            return []
        except Exception as e:
            logger.error(f"Text region extraction failed: {e}")
            return []

    def _detect_ui_elements(self, image_path: str) -> list[UIElement]:
        """Detect UI elements on screen."""
        elements = []

        # Try using accessibility APIs first
        try:
            elements.extend(self._detect_via_accessibility())
        except Exception as e:
            logger.debug(f"Accessibility detection failed: {e}")

        # Fallback: detect via image analysis
        if not elements:
            elements.extend(self._detect_via_image(image_path))

        return elements

    def _detect_via_accessibility(self) -> list[UIElement]:
        """Detect UI elements via OS accessibility APIs."""
        elements = []
        try:
            import platform
            system = platform.system()

            if system == "Linux":
                # Use AT-SPI via pyatspi or dbus
                try:
                    import pyatspi
                    # Get desktop elements
                    desktop = pyatspi.Registry.getDesktop(0)
                    for app in desktop:
                        elements.extend(self._traverse_accessibility_tree(app))
                except ImportError:
                    pass

            elif system == "Darwin":
                # Use macOS accessibility via pyobjc
                try:
                    from ApplicationServices import AXUIElementCreateSystemWide
                    system_wide = AXUIElementCreateSystemWide()
                    # Traverse accessibility tree
                    pass
                except ImportError:
                    pass

            elif system == "Windows":
                # Use UIAutomation via pywinauto or comtypes
                try:
                    from pywinauto import Desktop
                    desktop = Desktop(backend="uia")
                    for window in desktop.windows():
                        elements.extend(self._traverse_windows_uia(window))
                except ImportError:
                    pass

        except Exception as e:
            logger.debug(f"Accessibility detection error: {e}")

        return elements

    def _traverse_accessibility_tree(self, element: Any, depth: int = 0) -> list[UIElement]:
        """Recursively traverse accessibility tree."""
        elements = []
        if depth > 10:  # Limit depth
            return elements

        try:
            role = element.getRoleName()
            name = element.name or ""
            state = element.getState()

            # Map accessibility roles to UI element types
            type_map = {
                "push button": "button",
                "check box": "checkbox",
                "radio button": "radio",
                "text": "text_field",
                "menu": "menu",
                "menu item": "menu_item",
                "link": "link",
                "image": "image",
                "label": "label",
                "combo box": "dropdown",
                "list": "list",
                "list item": "list_item",
                "table": "table",
                "tree": "tree",
                "slider": "slider",
                "spin box": "spinbox",
                "tab": "tab",
                "tab page": "tab_page",
                "tool bar": "toolbar",
                "status bar": "statusbar",
                "scroll bar": "scrollbar",
                "progress bar": "progressbar",
            }

            ui_type = type_map.get(role.lower(), "unknown")

            # Get bounding box if available
            try:
                ext = element.queryComponent().getExtents(0)  # Screen coordinates
                x, y, w, h = ext.x, ext.y, ext.width, ext.height
            except Exception:
                x, y, w, h = 0, 0, 0, 0

            ui_element = UIElement(
                element_type=ui_type,
                text=name,
                x=x, y=y, width=w, height=h,
                clickable=role.lower() in ("push button", "check box", "radio button", "link", "menu item"),
                enabled=state.contains(pyatspi.STATE_ENABLED) if hasattr(state, 'contains') else True,
                confidence=0.9,
            )
            elements.append(ui_element)

            # Traverse children
            for i in range(element.childCount):
                elements.extend(self._traverse_accessibility_tree(element.getChildAtIndex(i), depth + 1))

        except Exception as e:
            logger.debug(f"Accessibility traversal error: {e}")

        return elements

    def _traverse_windows_uia(self, element: Any, depth: int = 0) -> list[UIElement]:
        """Traverse Windows UIA tree."""
        elements = []
        if depth > 10:
            return elements

        try:
            control_type = element.element_info.control_type
            name = element.element_info.name or ""

            type_map = {
                "Button": "button",
                "CheckBox": "checkbox",
                "RadioButton": "radio",
                "Edit": "text_field",
                "ComboBox": "dropdown",
                "List": "list",
                "ListItem": "list_item",
                "Menu": "menu",
                "MenuItem": "menu_item",
                "Image": "image",
                "Text": "label",
                "Tab": "tab",
                "TabItem": "tab_page",
                "Slider": "slider",
                "ProgressBar": "progressbar",
                "ScrollBar": "scrollbar",
                "StatusBar": "statusbar",
                "ToolBar": "toolbar",
                "Tree": "tree",
                "TreeItem": "tree_item",
                "Hyperlink": "link",
                "Custom": "custom",
            }

            ui_type = type_map.get(control_type, "unknown")
            rect = element.rectangle()

            ui_element = UIElement(
                element_type=ui_type,
                text=name,
                x=rect.left, y=rect.top,
                width=rect.width(), height=rect.height(),
                clickable=control_type in ("Button", "CheckBox", "RadioButton", "Hyperlink", "MenuItem"),
                enabled=element.element_info.is_enabled,
                confidence=0.9,
            )
            elements.append(ui_element)

            for child in element.children():
                elements.extend(self._traverse_windows_uia(child, depth + 1))

        except Exception as e:
            logger.debug(f"UIA traversal error: {e}")

        return elements

    def _detect_via_image(self, image_path: str) -> list[UIElement]:
        """Detect UI elements via image analysis (fallback)."""
        elements = []
        try:
            from PIL import Image
            import pytesseract

            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            # Group text into regions
            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                if text and data["conf"][i] > 30:
                    elements.append(UIElement(
                        element_type="text",
                        text=text,
                        x=data["left"][i],
                        y=data["top"][i],
                        width=data["width"][i],
                        height=data["height"][i],
                        clickable=False,
                        confidence=data["conf"][i] / 100.0,
                    ))

        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Image detection error: {e}")

        return elements

    def find_element(self, text: str, element_type: str | None = None) -> UIElement | None:
        """Find a UI element by text."""
        self.pm.require(Permission.VISION_CAPTURE)
        analysis = self.capture_and_analyze()

        for elem_dict in analysis.get("ui_elements", []):
            if text.lower() in elem_dict.get("text", "").lower():
                if element_type is None or elem_dict.get("type") == element_type:
                    return UIElement(
                        element_type=elem_dict["type"],
                        text=elem_dict["text"],
                        x=elem_dict["x"],
                        y=elem_dict["y"],
                        width=elem_dict["width"],
                        height=elem_dict["height"],
                        clickable=elem_dict["clickable"],
                        enabled=elem_dict["enabled"],
                        confidence=elem_dict["confidence"],
                    )
        return None

    def find_all_clickable(self) -> list[UIElement]:
        """Find all clickable elements on screen."""
        self.pm.require(Permission.VISION_CAPTURE)
        analysis = self.capture_and_analyze()

        clickable = []
        for elem_dict in analysis.get("ui_elements", []):
            if elem_dict.get("clickable"):
                clickable.append(UIElement(
                    element_type=elem_dict["type"],
                    text=elem_dict["text"],
                    x=elem_dict["x"],
                    y=elem_dict["y"],
                    width=elem_dict["width"],
                    height=elem_dict["height"],
                    clickable=True,
                    enabled=elem_dict["enabled"],
                    confidence=elem_dict["confidence"],
                ))
        return clickable

    def get_screen_text(self) -> str:
        """Get all text visible on screen."""
        self.pm.require(Permission.VISION_CAPTURE)
        screenshot_path = self._capture_screenshot()
        if screenshot_path:
            return self._run_ocr(screenshot_path)
        return ""

    def read_screen_region(self, x: int, y: int, width: int, height: int) -> str:
        """Read text from a specific screen region."""
        self.pm.require(Permission.VISION_CAPTURE)
        try:
            import pyautogui
            import pytesseract
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            return pytesseract.image_to_string(screenshot).strip()
        except ImportError:
            return "[OCR unavailable]"
        except Exception as e:
            return f"[Error: {e}]"

    def wait_for_text(self, text: str, timeout: float = 10.0, interval: float = 1.0) -> bool:
        """Wait for specific text to appear on screen."""
        self.pm.require(Permission.VISION_CAPTURE)
        start = time.time()
        while time.time() - start < timeout:
            screen_text = self.get_screen_text()
            if text.lower() in screen_text.lower():
                return True
            time.sleep(interval)
        return False

    def wait_for_element(self, text: str, timeout: float = 10.0, interval: float = 1.0) -> UIElement | None:
        """Wait for a UI element to appear."""
        self.pm.require(Permission.VISION_CAPTURE)
        start = time.time()
        while time.time() - start < timeout:
            element = self.find_element(text)
            if element:
                return element
            time.sleep(interval)
        return None


_screen_understanding: ScreenUnderstanding | None = None


def get_screen_understanding() -> ScreenUnderstanding:
    global _screen_understanding
    if _screen_understanding is None:
        _screen_understanding = ScreenUnderstanding()
    return _screen_understanding
