import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.constants import DATA_DIR
from shared.logger import logger

ZONES_FILE = Path(DATA_DIR) / "zones.json"

class ZoneStore:
    def __init__(self, file_path: Path = ZONES_FILE):
        self.file_path = file_path
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            default_zones = [
                {
                    "id": "z1",
                    "camera_id": "cam1",
                    "name": "Border line",
                    "points": [[0.1, 0.6], [0.9, 0.6], [0.9, 0.9], [0.1, 0.9]],
                    "classes": ["person", "vehicle"],
                    "enabled": True
                }
            ]
            self._save_zones_unlocked(default_zones)

    def _load_zones_unlocked(self) -> List[Dict[str, Any]]:
        try:
            if self.file_path.exists():
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading zones from {self.file_path}: {e}")
        return []

    def _save_zones_unlocked(self, zones: List[Dict[str, Any]]):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(zones, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving zones to {self.file_path}: {e}")

    def list_zones(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            zones = self._load_zones_unlocked()
            if camera_id:
                return [z for z in zones if z.get("camera_id") == camera_id]
            return zones

    def get_zone(self, zone_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            zones = self._load_zones_unlocked()
            for z in zones:
                if z.get("id") == zone_id:
                    return z
            return None

    def add_zone(self, zone_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            zones = self._load_zones_unlocked()
            zone_id = zone_data.get("id")
            if not zone_id:
                existing_ids = [int(z["id"][1:]) for z in zones if z.get("id", "").startswith("z") and z["id"][1:].isdigit()]
                next_num = (max(existing_ids) + 1) if existing_ids else len(zones) + 1
                zone_id = f"z{next_num}"

            new_zone = {
                "id": zone_id,
                "camera_id": zone_data.get("camera_id", "cam1"),
                "name": zone_data.get("name", f"Zone {zone_id}"),
                "points": zone_data.get("points", [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]]),
                "classes": zone_data.get("classes", ["person", "vehicle"]),
                "enabled": zone_data.get("enabled", True)
            }
            zones.append(new_zone)
            self._save_zones_unlocked(zones)
            return new_zone

    def update_zone(self, zone_id: str, zone_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self._lock:
            zones = self._load_zones_unlocked()
            updated_zone = None
            for z in zones:
                if z.get("id") == zone_id:
                    if "name" in zone_data:
                        z["name"] = zone_data["name"]
                    if "points" in zone_data:
                        z["points"] = zone_data["points"]
                    if "classes" in zone_data:
                        z["classes"] = zone_data["classes"]
                    if "enabled" in zone_data:
                        z["enabled"] = zone_data["enabled"]
                    if "camera_id" in zone_data:
                        z["camera_id"] = zone_data["camera_id"]
                    updated_zone = z
                    break
            if updated_zone:
                self._save_zones_unlocked(zones)
            return updated_zone

    def delete_zone(self, zone_id: str) -> bool:
        with self._lock:
            zones = self._load_zones_unlocked()
            initial_count = len(zones)
            zones = [z for z in zones if z.get("id") != zone_id]
            if len(zones) < initial_count:
                self._save_zones_unlocked(zones)
                return True
            return False

# Global instance
zone_store = ZoneStore()
