import time
import cv2
import numpy as np
from typing import Generator, Optional
from shared.schemas import FrameContext, ObjectClass
from shared.constants import GROUP_COLORS
from shared.logger import logger

class Streamer:
    def __init__(self):
        pass

    def draw_overlay(self, ctx: FrameContext) -> np.ndarray:
        """Draws bounding boxes and labels on frame.
        
        Labels:
        - If tracking is on (tracks exist): "#<id> <label>"
        - If tracking is off (only detections exist): "<label>"
        Colors:
        - Person: Green (0, 255, 0)
        - Vehicle: Orange (0, 165, 255)
        - Animal: Yellow (0, 255, 255)
        - Object: Purple (211, 0, 148)
        """
        if ctx.frame is None:
            return None
        frame = ctx.frame.copy()

        # If tracks are available, draw tracks with #<id> <label>
        if ctx.tracks:
            for trk in ctx.tracks:
                x1, y1, x2, y2 = trk.bbox
                color = GROUP_COLORS.get(trk.cls, (0, 255, 0))
                lbl = trk.label if trk.label else trk.cls.value
                label = f"#{trk.track_id} {lbl}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, max(y1 - 5, 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        elif ctx.detections:
            # If tracking is off or no tracks, draw plain detections
            for det in ctx.detections:
                x1, y1, x2, y2 = det.bbox
                color = GROUP_COLORS.get(det.cls, (0, 255, 0))
                lbl = det.label if det.label else det.cls.value
                label = f"{lbl}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, max(y1 - 5, 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return frame

    def encode_jpeg(self, frame: np.ndarray, quality: int = 70) -> Optional[bytes]:
        try:
            ret, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            if ret:
                return buf.tobytes()
        except Exception as e:
            logger.error(f"Error encoding frame to JPEG: {e}")
        return None

def generate_mjpeg_stream(camera_manager, camera_id: str, pipeline=None) -> Generator[bytes, None, None]:
    last_ts = 0.0
    streamer = Streamer()
    while True:
        reader = camera_manager.get_reader(camera_id)
        if reader and reader.is_online():
            latest = reader.get_latest_frame()
            if latest is not None:
                frame, ts = latest
                if ts > last_ts:
                    last_ts = ts
                    
                    # Draw overlay from pipeline if available
                    annotated_frame = frame
                    if pipeline is not None:
                        ctx = pipeline.get_latest_context(camera_id)
                        if ctx is not None:
                            # Attach latest frame copy to ctx for overlay drawing
                            ctx_copy = FrameContext(
                                camera_id=ctx.camera_id,
                                frame_id=ctx.frame_id,
                                timestamp=ctx.timestamp,
                                frame=frame,
                                detections=ctx.detections,
                                tracks=ctx.tracks,
                                events=ctx.events,
                                extras=ctx.extras
                            )
                            drawn = streamer.draw_overlay(ctx_copy)
                            if drawn is not None:
                                annotated_frame = drawn

                    # Encode JPEG frame with quality 70 for low latency
                    jpeg_bytes = streamer.encode_jpeg(annotated_frame, quality=70)
                    if jpeg_bytes:
                        yield (
                            b"--frame\r\n"
                            b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
                        )
        time.sleep(0.03)  # ~30 FPS streaming loop
