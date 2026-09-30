import time
import cv2
import numpy as np
from typing import Generator, Optional
from shared.schemas import FrameContext
from shared.logger import logger

class Streamer:
    def __init__(self):
        pass

    def draw_overlay(self, ctx: FrameContext) -> np.ndarray:
        """Draws bounding boxes, labels, zones on the frame."""
        frame = ctx.frame.copy()
        
        # Draw detections if any
        for det in ctx.detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, f"{det.cls.value} {det.conf:.2f}", (x1, max(y1 - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        # Draw tracks if any
        for trk in ctx.tracks:
            x1, y1, x2, y2 = trk.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID:{trk.track_id} {trk.cls.value}", (x1, max(y1 - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return frame

    def encode_jpeg(self, frame: np.ndarray, quality: int = 70) -> Optional[bytes]:
        try:
            ret, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            if ret:
                return buf.tobytes()
        except Exception as e:
            logger.error(f"Error encoding frame to JPEG: {e}")
        return None

def generate_mjpeg_stream(camera_manager, camera_id: str) -> Generator[bytes, None, None]:
    last_ts = 0.0
    while True:
        reader = camera_manager.get_reader(camera_id)
        if reader and reader.is_online():
            latest = reader.get_latest_frame()
            if latest is not None:
                frame, ts = latest
                if ts > last_ts:
                    last_ts = ts
                    # Encode frame with quality 70 for low latency
                    _, jpeg_buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    jpeg_bytes = jpeg_buf.tobytes()
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
                    )
        time.sleep(0.03) # ~30 FPS polling loop
