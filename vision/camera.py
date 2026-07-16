"""
JARVIS OS - Camera & Face Detection
=====================================

Camera capture and face/environment recognition.

Features:
- Camera capture (photo + video)
- Face detection and recognition
- Motion detection
- Environment analysis
- QR/barcode scanning
- Object detection
"""

from __future__ import annotations

import base64
import io
import time
from pathlib import Path
from typing import Any

from loguru import logger

from core.config import get_settings
from core.security import get_permission_manager, Permission, AuditEventType, get_audit_logger


@dataclass
class DetectedFace:
    """Represents a detected face."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    name: str | None = None
    encoding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": self.x, "y": self.y,
            "width": self.width, "height": self.height,
            "confidence": self.confidence,
            "name": self.name,
        }


from dataclasses import dataclass


class CameraEngine:
    """Camera capture and face detection engine."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.pm = get_permission_manager()
        self.audit = get_audit_logger()
        self._camera = None
        self._face_cascade = None
        self._known_faces: dict[str, list[float]] = {}
        self._camera_index = 0

    def initialize(self) -> bool:
        """Initialize camera and face detection."""
        self.pm.require(Permission.VISION_CAPTURE)

        # Try OpenCV for camera
        try:
            import cv2
            self._camera = cv2.VideoCapture(self._camera_index)
            if self._camera.isOpened():
                logger.success("Camera initialized (OpenCV)")
            else:
                logger.warning("Camera not available")
                self._camera = None
        except ImportError:
            logger.debug("OpenCV not available for camera")

        # Try face detection
        try:
            import cv2
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
            logger.success("Face detection ready (Haar cascade)")
        except Exception as e:
            logger.debug(f"Face detection init: {e}")

        # Try face_recognition library
        try:
            import face_recognition
            logger.success("Face recognition library available")
        except ImportError:
            pass

        return True

    def capture_photo(self) -> dict[str, Any]:
        """Capture a single photo."""
        self.pm.require(Permission.VISION_CAPTURE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "capture_photo"})

        try:
            import cv2
            from PIL import Image

            if self._camera and self._camera.isOpened():
                ret, frame = self._camera.read()
                if ret:
                    # Convert BGR to RGB
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb_frame)

                    # Save
                    path = self.settings.base_dir / "temp" / f"photo_{int(time.time())}.jpg"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    img.save(str(path))

                    # Base64 encode
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG")
                    b64 = base64.b64encode(buf.getvalue()).decode()

                    return {
                        "success": True,
                        "path": str(path),
                        "base64": b64,
                        "width": img.width,
                        "height": img.height,
                    }
            else:
                # Fallback: use pyautogui screenshot
                import pyautogui
                path = self.settings.base_dir / "temp" / f"photo_{int(time.time())}.jpg"
                path.parent.mkdir(parents=True, exist_ok=True)
                screenshot = pyautogui.screenshot()
                screenshot.save(str(path))

                buf = io.BytesIO()
                screenshot.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode()

                return {
                    "success": True,
                    "path": str(path),
                    "base64": b64,
                    "width": screenshot.width,
                    "height": screenshot.height,
                    "note": "Using screenshot (camera unavailable)",
                }
        except Exception as e:
            logger.error(f"Photo capture failed: {e}")
            return {"success": False, "error": str(e)}

    def detect_faces(self) -> list[DetectedFace]:
        """Detect faces in current camera frame."""
        self.pm.require(Permission.VISION_CAPTURE)
        self.pm.require(Permission.VISION_ANALYZE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "detect_faces"})

        faces = []
        try:
            import cv2

            if self._camera and self._camera.isOpened():
                ret, frame = self._camera.read()
                if ret and self._face_cascade:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    detected = self._face_cascade.detectMultiScale(
                        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                    )
                    for (x, y, w, h) in detected:
                        faces.append(DetectedFace(
                            x=int(x), y=int(y),
                            width=int(w), height=int(h),
                            confidence=0.85,
                        ))
        except ImportError:
            logger.debug("OpenCV not available for face detection")
        except Exception as e:
            logger.error(f"Face detection failed: {e}")

        return faces

    def recognize_faces(self) -> list[DetectedFace]:
        """Recognize known faces in current frame."""
        self.pm.require(Permission.VISION_CAPTURE)
        self.pm.require(Permission.VISION_ANALYZE)

        faces = []
        try:
            import face_recognition
            import cv2

            if self._camera and self._camera.isOpened():
                ret, frame = self._camera.read()
                if ret:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_frame)
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                    for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
                        name = None
                        for known_name, known_encoding in self._known_faces.items():
                            matches = face_recognition.compare_faces([known_encoding], encoding)
                            if matches[0]:
                                name = known_name
                                break

                        faces.append(DetectedFace(
                            x=left, y=top,
                            width=right - left, height=bottom - top,
                            confidence=0.9,
                            name=name,
                            encoding=encoding.tolist(),
                        ))
        except ImportError:
            logger.debug("face_recognition library not available")
        except Exception as e:
            logger.error(f"Face recognition failed: {e}")

        return faces

    def register_face(self, name: str, image_path: str | None = None) -> bool:
        """Register a new known face."""
        self.pm.require(Permission.VISION_CAPTURE)
        self.pm.require(Permission.MEMORY_WRITE)
        self.audit.log_event(AuditEventType.AUTOMATION_ACTION, details={"action": "register_face", "name": name})

        try:
            import face_recognition

            if image_path:
                image = face_recognition.load_image_file(image_path)
            else:
                import cv2
                if self._camera and self._camera.isOpened():
                    ret, frame = self._camera.read()
                    if ret:
                        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    else:
                        return False
                else:
                    return False

            encodings = face_recognition.face_encodings(image)
            if encodings:
                self._known_faces[name] = encodings[0]
                self._save_known_faces()
                logger.info(f"Face registered: {name}")
                return True
            return False
        except ImportError:
            logger.warning("face_recognition not available")
            return False
        except Exception as e:
            logger.error(f"Face registration failed: {e}")
            return False

    def _save_known_faces(self) -> None:
        """Save known faces to disk."""
        path = self.settings.base_dir / self.settings.data_dir / "known_faces.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        data = {name: enc.tolist() if hasattr(enc, 'tolist') else enc
                for name, enc in self._known_faces.items()}
        path.write_text(json.dumps(data), encoding="utf-8")

    def _load_known_faces(self) -> None:
        """Load known faces from disk."""
        path = self.settings.base_dir / self.settings.data_dir / "known_faces.json"
        if path.exists():
            import json
            data = json.loads(path.read_text())
            self._known_faces = {name: enc for name, enc in data.items()}

    def scan_qr(self) -> list[str]:
        """Scan for QR codes in current frame."""
        self.pm.require(Permission.VISION_CAPTURE)
        results = []
        try:
            import cv2
            from pyzbar import pyzbar

            if self._camera and self._camera.isOpened():
                ret, frame = self._camera.read()
                if ret:
                    decoded = pyzbar.decode(frame)
                    for obj in decoded:
                        results.append(obj.data.decode("utf-8"))
        except ImportError:
            logger.debug("pyzbar not available for QR scanning")
        except Exception as e:
            logger.error(f"QR scan failed: {e}")
        return results

    def detect_motion(self, threshold: float = 0.05) -> bool:
        """Detect motion between frames."""
        self.pm.require(Permission.VISION_CAPTURE)
        try:
            import cv2
            import numpy as np

            if self._camera and self._camera.isOpened():
                ret, frame1 = self._camera.read()
                time.sleep(0.1)
                ret, frame2 = self._camera.read()

                if ret:
                    diff = cv2.absdiff(
                        cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY),
                        cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
                    )
                    motion = np.mean(diff) / 255.0
                    return motion > threshold
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Motion detection error: {e}")
        return False

    def analyze_environment(self) -> dict[str, Any]:
        """Analyze the environment (lighting, objects, etc.)."""
        self.pm.require(Permission.VISION_CAPTURE)
        self.pm.require(Permission.VISION_ANALYZE)

        result = self.capture_photo()
        if not result.get("success"):
            return {"success": False, "error": "Capture failed"}

        try:
            from PIL import Image, ImageStat
            img = Image.open(result["path"])

            # Basic analysis
            stat = ImageStat.Stat(img)
            brightness = stat.mean[0] if stat.mean else 0

            return {
                "success": True,
                "brightness": brightness,
                "brightness_level": "bright" if brightness > 150 else "dim" if brightness > 50 else "dark",
                "resolution": f"{img.width}x{img.height}",
                "mode": img.mode,
                "faces_detected": len(self.detect_faces()),
            }
        except Exception as e:
            logger.error(f"Environment analysis failed: {e}")
            return {"success": False, "error": str(e)}

    def release(self) -> None:
        """Release camera resources."""
        if self._camera:
            try:
                self._camera.release()
            except Exception:
                pass
            self._camera = None

    def get_status(self) -> dict[str, Any]:
        """Get camera status."""
        return {
            "camera_available": self._camera is not None and self._camera.isOpened(),
            "face_detection": self._face_cascade is not None,
            "known_faces": len(self._known_faces),
            "camera_index": self._camera_index,
        }


_camera: CameraEngine | None = None


def get_camera() -> CameraEngine:
    global _camera
    if _camera is None:
        _camera = CameraEngine()
    return _camera
