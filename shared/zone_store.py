import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.constants import DATA_DIR
from shared.logger import logger

ZONES_FILE = Path(DATA_DIR) / "zones.json"

def check_segment_intersection(p1: List[float], p2: List[float], p3: List[float], p4: List[float]) -> bool:
    """Returns True if line segment p1-p2 intersects line segment p3-p4."""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))

def validate_polygon_geometry(points: List[List[float]], ztype: str = "polygon") -> tuple[bool, str]:
    if ztype == "line":
        if len(points) < 2:
            return False, "Tripwire line requires at least 2 points."
        return True, ""

    if len(points) < 3:
        return False, "Polygon requires at least 3 vertices."

    # Check for near-zero area using Shoelace formula
    n = len(points)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1] - points[j][0] * points[i][1]
    area = abs(area) * 0.5
    if area < 0.0005:  # Less than 0.05% of frame area
        return False, "Shape area is too small."

    # Check for self-intersecting edges
    edges = [(points[i], points[(i + 1) % n]) for i in range(n)]
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue  # adjacent end edges
            if check_segment_intersection(edges[i][0], edges[i][1], edges[j][0], edges[j][1]):
                return False, "Polygon has self-intersecting edges."

    return True, ""

def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return round(max(min_val, min(max_val, val)), 4)

def move_vertex(points: List[List[float]], index: int, new_point: List[float]) -> List[List[float]]:
    res = [list(p) for p in points]
    if 0 <= index < len(res):
        res[index] = [clamp(new_point[0]), clamp(new_point[1])]
    return res

def insert_vertex(points: List[List[float]], edge_index: int, new_point: List[float]) -> List[List[float]]:
    res = [list(p) for p in points]
    insert_pos = edge_index + 1
    res.insert(insert_pos, [clamp(new_point[0]), clamp(new_point[1])])
    return res

def delete_vertex(points: List[List[float]], index: int, ztype: str = "polygon") -> List[List[float]]:
    min_points = 2 if ztype == "line" else 3
    if len(points) <= min_points:
        return [list(p) for p in points]  # Keep minimum required points
    res = [list(p) for p in points]
    if 0 <= index < len(res):
        res.pop(index)
    return res

def move_whole_zone(points: List[List[float]], dx: float, dy: float) -> List[List[float]]:
    if not points:
        return []
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)

    clamped_dx = max(-min_x, min(1.0 - max_x, dx))
    clamped_dy = max(-min_y, min(1.0 - max_y, dy))

    return [[clamp(p[0] + clamped_dx), clamp(p[1] + clamped_dy)] for p in points]

def resize_rectangle(points: List[List[float]], handle: str, new_x: float, new_y: float) -> List[List[float]]:
    if not points:
        return []
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)

    nx, ny = clamp(new_x), clamp(new_y)

    if 'n' in handle:
        min_y = min(ny, max_y - 0.02)
    if 's' in handle:
        max_y = max(ny, min_y + 0.02)
    if 'w' in handle:
        min_x = min(nx, max_x - 0.02)
    if 'e' in handle:
        max_x = max(nx, min_x + 0.02)

    return [
        [min_x, min_y],
        [max_x, min_y],
        [max_x, max_y],
        [min_x, max_y]
    ]

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
                    "enabled": True,
                    "type": "polygon",
                    "color": "#ef4444",
                    "direction": "both"
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
                "enabled": zone_data.get("enabled", True),
                "type": zone_data.get("type", "polygon"),
                "color": zone_data.get("color", "#ef4444"),
                "direction": zone_data.get("direction", "both")
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
                    if "type" in zone_data:
                        z["type"] = zone_data["type"]
                    if "color" in zone_data:
                        z["color"] = zone_data["color"]
                    if "direction" in zone_data:
                        z["direction"] = zone_data["direction"]
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
