import time
import numpy as np
import cv2
from core.ingest import CameraReader

def test_camera_reader_latest_frame_only():
    reader = CameraReader(camera_id="test_cam", cam_type="phone", source="")
    
    # Create two dummy frames
    f1 = np.zeros((480, 640, 3), dtype=np.uint8)
    f2 = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    _, buf1 = cv2.imencode(".jpg", f1)
    _, buf2 = cv2.imencode(".jpg", f2)

    reader.push_jpeg(buf1.tobytes())
    time.sleep(0.01)
    reader.push_jpeg(buf2.tobytes())

    latest = reader.get_latest_frame()
    assert latest is not None
    frame, ts = latest
    # Verify latest frame is f2 (white frame)
    assert np.mean(frame) > 200
    assert reader.is_online() is True
