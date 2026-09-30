import pytest
from pathlib import Path
from core.camera_manager import CameraManager

def test_camera_crud(tmp_path, monkeypatch):
    test_json = tmp_path / "cameras.json"
    monkeypatch.setattr("core.camera_manager.CAMERAS_JSON_PATH", test_json)

    cm = CameraManager(config_path="non_existent.yaml")
    assert len(cm.list_cameras()) == 0

    # Add camera
    cam = cm.add_camera(name="Test Webcam", cam_type="webcam", source="0", enabled=False)
    assert cam["id"] == "cam1"
    assert cam["name"] == "Test Webcam"
    assert len(cm.list_cameras()) == 1

    # Update camera
    updated = cm.update_camera(cam_id="cam1", name="Updated Name")
    assert updated["name"] == "Updated Name"

    # Delete camera
    deleted = cm.delete_camera("cam1")
    assert deleted is True
    assert len(cm.list_cameras()) == 0
