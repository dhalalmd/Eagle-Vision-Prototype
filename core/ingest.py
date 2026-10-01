import time
import threading
import sys
import cv2
import numpy as np
from typing import Optional, Tuple
from shared.logger import logger
from core.image_adjust import apply_settings, DEFAULT_SETTINGS

class CameraReader:
    def __init__(self, camera_id: str, cam_type: str, source: str,
                 settings: Optional[dict] = None):
        self.camera_id = camera_id
        self.cam_type = cam_type
        self.source = source
        self.settings = settings or dict(DEFAULT_SETTINGS)
        self.running = False
        self.thread: Optional[threading.Thread] = None

        self._latest_frame: Optional[np.ndarray] = None
        self._latest_jpeg: Optional[bytes] = None
        self._last_frame_time: float = 0.0
        self._lock = threading.Lock()
        
        self.fps: float = 0.0
        self._frame_count: int = 0
        self._fps_start_time: float = time.time()

    def start(self):
        if self.running:
            return
        self.running = True
        if self.cam_type != "phone":
            self.thread = threading.Thread(target=self._reader_loop, daemon=True, name=f"Reader-{self.camera_id}")
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def is_online(self) -> bool:
        if self._last_frame_time == 0:
            return False
        return (time.time() - self._last_frame_time) < 3.0

    def get_last_frame_age_ms(self) -> float:
        if self._last_frame_time == 0:
            return 99999.0
        return (time.time() - self._last_frame_time) * 1000.0

    def get_latest_frame(self) -> Optional[Tuple[np.ndarray, float]]:
        with self._lock:
            if self._latest_frame is None:
                return None
            return self._latest_frame.copy(), self._last_frame_time

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def push_jpeg(self, jpeg_bytes: bytes):
        """Used by phone camera WebSocket to push JPEG frames."""
        try:
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is not None:
                self._update_frame(frame)
        except Exception as e:
            logger.error(f"Error decoding phone JPEG for camera {self.camera_id}: {e}")

    def _update_frame(self, frame: np.ndarray):
        # Resize to max 640px wide for low latency
        h, w = frame.shape[:2]
        if w > 640:
            new_w = 640
            new_h = int(h * (640 / w))
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Apply image settings before FrameContext is built
        frame = apply_settings(frame, self.settings)

        # Encode JPEG once, share across viewers
        _, jpeg_buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        raw_jpeg = jpeg_buf.tobytes()

        now = time.time()
        with self._lock:
            self._latest_frame = frame
            self._latest_jpeg = raw_jpeg
            self._last_frame_time = now

        # Update FPS calculation
        self._frame_count += 1
        elapsed = now - self._fps_start_time
        if elapsed >= 1.0:
            self.fps = round(self._frame_count / elapsed, 1)
            self._frame_count = 0
            self._fps_start_time = now

    def _open_capture(self) -> Optional[cv2.VideoCapture]:
        cap = None
        if self.cam_type == "webcam":
            try:
                dev_idx = int(self.source)
            except ValueError:
                dev_idx = 0
            if sys.platform.startswith("win"):
                cap = cv2.VideoCapture(dev_idx, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(dev_idx)
        elif self.cam_type in ("url", "file"):
            cap = cv2.VideoCapture(self.source)
        
        if cap and cap.isOpened():
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        return None

    def _reader_loop(self):
        backoff = 1.0
        while self.running:
            cap = self._open_capture()
            if cap is None or not cap.isOpened():
                logger.warning(f"Failed to open source '{self.source}' for camera {self.camera_id}. Retrying in {backoff:.1f}s...")
                time.sleep(backoff)
                backoff = min(backoff * 1.5, 10.0)
                continue

            backoff = 1.0
            logger.info(f"Camera reader connected: {self.camera_id} ({self.source})")

            while self.running and cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame is None:
                    if self.cam_type == "file":
                        # Loop video file
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        logger.warning(f"Frame read failure on camera {self.camera_id}")
                        break
                
                self._update_frame(frame)
                # Keep FPS target around 25-30
                time.sleep(0.01)

            cap.release()
            if self.running:
                logger.warning(f"Connection lost for camera {self.camera_id}. Reconnecting...")
                time.sleep(1.0)
