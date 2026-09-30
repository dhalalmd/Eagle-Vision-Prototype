import pytest
import numpy as np
import cv2
from fastapi.testclient import TestClient
import backend.api as api_module
import backend.ws as ws_module
from backend.main import app
from core.camera_manager import CameraManager

def test_phone_websocket_accepts_frames(tmp_path, monkeypatch):
    test_json = tmp_path / "cameras.json"
    monkeypatch.setattr("core.camera_manager.CAMERAS_JSON_PATH", test_json)

    cm = CameraManager(config_path="non_existent.yaml")
    api_module.camera_manager = cm
    ws_module.camera_manager = cm

    client = TestClient(app)

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", dummy_frame)
    jpeg_bytes = buf.tobytes()

    with client.websocket_connect("/ws/phone/phone1") as websocket:
        websocket.send_bytes(jpeg_bytes)

    reader = cm.get_reader("phone1")
    assert reader is not None
    assert reader.is_online() is True
