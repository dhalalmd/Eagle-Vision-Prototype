import json
import time
import threading
import sys
import cv2
from pathlib import Path
from typing import Dict, List, Optional, Any

from shared.logger import logger
from shared.config import load_config
from core.ingest import CameraReader

CAMERAS_JSON_PATH = Path("data/cameras.json")

class CameraManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.lock = threading.Lock()
        self.cameras: Dict[str, dict] = {}       # id -> camera record dict
        self.readers: Dict[str, CameraReader] = {} # id -> CameraReader instance

        self._ensure_storage()

    def _ensure_storage(self):
        Path("data").mkdir(parents=True, exist_ok=True)
        if not CAMERAS_JSON_PATH.exists():
            # Seed from config.yaml once
            cfg = load_config(self.config_path)
            seed_cams = cfg.get("cameras", [])
            for c in seed_cams:
                cam_id = c.get("id", f"cam{len(self.cameras)+1}")
                self.cameras[cam_id] = {
                    "id": cam_id,
                    "name": c.get("name", f"Camera {cam_id}"),
                    "type": c.get("type", "webcam"),
                    "source": str(c.get("source", "0")),
                    "enabled": bool(c.get("enabled", True))
                }
            self._save_cameras()
        else:
            try:
                with open(CAMERAS_JSON_PATH, "r", encoding="utf-8") as f:
                    cams = json.load(f)
                    for c in cams:
                        self.cameras[c["id"]] = c
            except Exception as e:
                logger.error(f"Failed to read {CAMERAS_JSON_PATH}: {e}")
                self.cameras = {}

        # Initialize readers for cameras
        for cam_id, cam in self.cameras.items():
            if cam.get("enabled", True):
                self._start_reader(cam)

    def _save_cameras(self):
        with open(CAMERAS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(list(self.cameras.values()), f, indent=2)

    def _start_reader(self, cam: dict):
        cam_id = cam["id"]
        if cam_id in self.readers:
            self.readers[cam_id].stop()
        reader = CameraReader(cam_id, cam["type"], cam["source"])
        self.readers[cam_id] = reader
        reader.start()

    def _stop_reader(self, cam_id: str):
        if cam_id in self.readers:
            reader = self.readers.pop(cam_id)
            reader.stop()

    def list_cameras(self) -> List[dict]:
        with self.lock:
            result = []
            for cam_id, cam in self.cameras.items():
                record = dict(cam)
                reader = self.readers.get(cam_id)
                if reader and cam.get("enabled", True):
                    online = reader.is_online()
                    record["status"] = "online" if online else ("connecting" if reader.running else "offline")
                    record["fps"] = reader.fps if online else 0.0
                    record["last_frame_age_ms"] = round(reader.get_last_frame_age_ms(), 1)
                else:
                    record["status"] = "offline"
                    record["fps"] = 0.0
                    record["last_frame_age_ms"] = 99999.0
                result.append(record)
            return result

    def get_camera(self, cam_id: str) -> Optional[dict]:
        cams = self.list_cameras()
        for c in cams:
            if c["id"] == cam_id:
                return c
        return None

    def add_camera(self, name: str, cam_type: str, source: str, enabled: bool = True, cam_id: Optional[str] = None) -> dict:
        with self.lock:
            if not cam_id:
                existing_ids = [c["id"] for c in self.cameras.values()]
                idx = 1
                while f"cam{idx}" in existing_ids:
                    idx += 1
                cam_id = f"cam{idx}"

            record = {
                "id": cam_id,
                "name": name,
                "type": cam_type,
                "source": str(source),
                "enabled": enabled
            }
            self.cameras[cam_id] = record
            self._save_cameras()

            if enabled:
                self._start_reader(record)

        return self.get_camera(cam_id)

    def update_camera(self, cam_id: str, name: Optional[str] = None, source: Optional[str] = None, enabled: Optional[bool] = None) -> Optional[dict]:
        with self.lock:
            if cam_id not in self.cameras:
                return None
            cam = self.cameras[cam_id]
            if name is not None:
                cam["name"] = name
            if source is not None:
                cam["source"] = str(source)
            if enabled is not None:
                cam["enabled"] = enabled

            self._save_cameras()

            if cam.get("enabled", True):
                self._start_reader(cam)
            else:
                self._stop_reader(cam_id)

        return self.get_camera(cam_id)

    def delete_camera(self, cam_id: str) -> bool:
        with self.lock:
            if cam_id not in self.cameras:
                return False
            self._stop_reader(cam_id)
            del self.cameras[cam_id]
            self._save_cameras()
            return True

    def get_reader(self, cam_id: str) -> Optional[CameraReader]:
        return self.readers.get(cam_id)

    def get_latest_jpeg(self, cam_id: str) -> Optional[bytes]:
        reader = self.readers.get(cam_id)
        if reader and reader.is_online():
            return reader.get_latest_jpeg()
        return None

    @staticmethod
    def probe_webcams() -> List[dict]:
        """Probes local webcam indexes 0-4."""
        webcams = []
        for idx in range(5):
            if sys.platform.startswith("win"):
                cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(idx)
            
            if cap and cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                if ret:
                    webcams.append({
                        "index": idx,
                        "name": f"Webcam {idx}"
                    })
        return webcams
