import pytest
import json
import numpy as np
from pathlib import Path
from core.camera_manager import CameraManager
from core.image_adjust import clamp_settings, apply_settings, DEFAULT_SETTINGS

def test_camera_crud(tmp_path, monkeypatch):
    test_json = tmp_path / "cameras.json"
    monkeypatch.setattr("core.camera_manager.CAMERAS_JSON_PATH", test_json)

    cm = CameraManager(config_path="non_existent.yaml")
    assert len(cm.list_cameras()) == 0

    # Add camera
    cam = cm.add_camera(name="Test Webcam", cam_type="webcam", source="0", enabled=False)
    assert cam["id"] == "cam1"
    assert cam["name"] == "Test Webcam"
    assert cam["settings"] == DEFAULT_SETTINGS
    assert len(cm.list_cameras()) == 1

    # Update camera
    updated = cm.update_camera(cam_id="cam1", name="Updated Name", settings={"brightness": 50, "contrast": 1.5})
    assert updated["name"] == "Updated Name"
    assert updated["settings"]["brightness"] == 50
    assert updated["settings"]["contrast"] == 1.5

    # Delete camera
    deleted = cm.delete_camera("cam1")
    assert deleted is True
    assert len(cm.list_cameras()) == 0

def test_settings_clamp_and_apply():
    # Test clamping
    raw = {
        "brightness": 200,    # max 100
        "contrast": 0.1,      # min 0.5
        "saturation": 5.0,    # max 2.0
        "zoom": 5.0,          # max 3.0
        "rotate": 45,         # invalid -> 0
        "flip_h": True,
        "flip_v": False,
        "grayscale": True,
        "invert_colors": True,
        "invalid_key": 999
    }
    clamped = clamp_settings(raw)
    assert clamped["brightness"] == 100
    assert clamped["contrast"] == 0.5
    assert clamped["saturation"] == 2.0
    assert clamped["zoom"] == 3.0
    assert clamped["rotate"] == 0
    assert clamped["flip_h"] is True
    assert "invalid_key" not in clamped

    # Test apply_settings transformations on a synthetic 100x100 BGR frame
    frame = np.full((100, 100, 3), 100, dtype=np.uint8)

    # Grayscale + Invert
    out = apply_settings(frame, {"grayscale": True, "invert_colors": True})
    assert out.shape == (100, 100, 3)
    assert np.all(out == 155)  # 255 - 100 = 155

    # Rotate 90
    rect_frame = np.zeros((100, 200, 3), dtype=np.uint8)
    rot_out = apply_settings(rect_frame, {"rotate": 90})
    assert rot_out.shape == (200, 100, 3)

def test_reset_settings(tmp_path, monkeypatch):
    test_json = tmp_path / "cameras.json"
    monkeypatch.setattr("core.camera_manager.CAMERAS_JSON_PATH", test_json)

    cm = CameraManager(config_path="non_existent.yaml")
    cm.add_camera(name="Cam Settings", cam_type="webcam", source="0", enabled=False)

    cm.update_camera("cam1", settings={"brightness": 80, "grayscale": True})
    updated = cm.get_camera("cam1")
    assert updated["settings"]["brightness"] == 80

    reset = cm.reset_settings("cam1")
    assert reset["settings"] == DEFAULT_SETTINGS

def test_old_camera_defaults(tmp_path, monkeypatch):
    test_json = tmp_path / "cameras.json"
    old_cams = [
        {"id": "cam_old", "name": "Old Camera", "type": "webcam", "source": "0", "enabled": False}
    ]
    test_json.write_text(json.dumps(old_cams), encoding="utf-8")
    monkeypatch.setattr("core.camera_manager.CAMERAS_JSON_PATH", test_json)

    cm = CameraManager(config_path="non_existent.yaml")
    cams = cm.list_cameras()
    assert len(cams) == 1
    assert cams[0]["id"] == "cam_old"
    assert cams[0]["settings"] == DEFAULT_SETTINGS
