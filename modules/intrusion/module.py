from typing import Dict, Tuple, List, Any
from modules.base import BaseModule
from shared.schemas import FrameContext, Event, EventType, Severity, ObjectClass
from shared.zone_store import zone_store
from shared.logger import logger

def is_point_in_polygon(x: float, y: float, polygon: List[List[float]]) -> bool:
    """Ray-casting algorithm for point in polygon test (0-1 normalized coords)."""
    n = len(polygon)
    if n < 3:
        return False
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

class Module(BaseModule):
    name = "intrusion"
    stage = "ana"
    order = 50
    requires = ("tracking",)

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.cooldown_s = float(self.cfg.get("cooldown_s", 10.0))
        # (camera_id, zone_id, track_id) -> last_fired_timestamp
        self.last_fired: Dict[Tuple[str, str, int], float] = {}

    def setup(self) -> None:
        self.last_fired.clear()
        logger.info(f"Intrusion detection module initialized (cooldown: {self.cooldown_s}s)")

    def process(self, ctx: FrameContext) -> None:
        if not ctx.camera_id or not ctx.tracks or ctx.frame is None:
            return

        h, w = ctx.frame.shape[:2]
        if h == 0 or w == 0:
            return

        zones = zone_store.list_zones(camera_id=ctx.camera_id)
        active_zones = [z for z in zones if z.get("enabled", True)]
        if not active_zones:
            return

        for trk in ctx.tracks:
            bx, by = trk.bottom_center
            nx, ny = bx / float(w), by / float(h)
            trk_label = trk.label if trk.label else trk.cls.value
            trk_group = trk.cls.value.lower()

            for zone in active_zones:
                zone_classes = [str(c).lower() for c in zone.get("classes", ["person", "vehicle"])]
                
                # Check if object group or label is allowed in zone
                if trk_group not in zone_classes and trk_label.lower() not in zone_classes:
                    continue

                poly = zone.get("points", [])
                if len(poly) < 3:
                    continue

                if is_point_in_polygon(nx, ny, poly):
                    key = (ctx.camera_id, zone["id"], trk.track_id)
                    last_time = self.last_fired.get(key, 0.0)
                    if (ctx.timestamp - last_time) >= self.cooldown_s:
                        self.last_fired[key] = ctx.timestamp

                        label_cap = trk_label.capitalize()
                        zone_name = zone.get("name", zone["id"])
                        cam_name = ctx.camera_id

                        msg = f'{label_cap} #{trk.track_id} entered zone "{zone_name}" on {cam_name}'
                        event = Event(
                            type=EventType.INTRUSION,
                            severity=Severity.HIGH,
                            camera_id=ctx.camera_id,
                            timestamp=ctx.timestamp,
                            frame_id=ctx.frame_id,
                            message=msg,
                            track_id=trk.track_id,
                            zone_id=zone["id"],
                            meta={
                                "label": trk_label,
                                "zone_name": zone_name,
                                "camera_name": cam_name
                            }
                        )
                        ctx.events.append(event)

    def teardown(self) -> None:
        self.last_fired.clear()
