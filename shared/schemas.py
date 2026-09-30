from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional
import numpy as np

class ObjectClass(str, Enum):
    PERSON = "person"
    VEHICLE = "vehicle"

class EventType(str, Enum):
    INTRUSION = "intrusion"
    LOITERING = "loitering"
    OBJECT_LEFT = "object_left"
    TAMPER = "tamper"
    ANPR = "anpr"
    REID_MATCH = "reid_match"
    FACE_MATCH = "face_match"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Detection:
    bbox: tuple[int, int, int, int]      # x1, y1, x2, y2 in PIXELS
    cls: ObjectClass
    conf: float                          # 0.0 - 1.0

@dataclass
class Track:
    track_id: int
    bbox: tuple[int, int, int, int]      # x1, y1, x2, y2 in PIXELS
    cls: ObjectClass
    conf: float

    @property
    def bottom_center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, y2)

@dataclass
class Event:
    type: EventType
    severity: Severity
    camera_id: str
    timestamp: float                     # epoch seconds (time.time())
    frame_id: int
    message: str = ""
    track_id: Optional[int] = None
    zone_id: Optional[str] = None
    evidence_path: Optional[str] = None  # set by evidence module
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class FrameContext:
    camera_id: str
    frame_id: int
    timestamp: float
    frame: np.ndarray                    # BGR (OpenCV order)
    detections: list[Detection] = field(default_factory=list)
    tracks: list[Track] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)   # extras[module_name] = output
