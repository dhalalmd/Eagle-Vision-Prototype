import time
import numpy as np
from shared.schemas import FrameContext, Track, Detection, ObjectClass

def make_ctx(camera_id="cam1", frame_id=0, frame=None, tracks=None,
             detections=None, ts=None):
    if frame is None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
    return FrameContext(
        camera_id=camera_id, frame_id=frame_id,
        timestamp=ts if ts is not None else time.time(),
        frame=frame, detections=detections or [], tracks=tracks or [])

def fake_track(track_id=1, bbox=(100, 100, 200, 300),
               cls=ObjectClass.PERSON, conf=0.9):
    return Track(track_id=track_id, bbox=bbox, cls=cls, conf=conf)

def fake_detection(bbox=(100, 100, 200, 300), cls=ObjectClass.PERSON, conf=0.9):
    return Detection(bbox=bbox, cls=cls, conf=conf)
