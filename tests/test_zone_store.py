import pytest
from pathlib import Path
from shared.zone_store import ZoneStore

def test_zone_store_crud(tmp_path):
    json_file = tmp_path / "zones.json"
    store = ZoneStore(file_path=json_file)

    # Initial state
    zones = store.list_zones()
    assert len(zones) >= 1

    # Add zone
    new_zone = store.add_zone({
        "camera_id": "cam1",
        "name": "Test Zone",
        "points": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        "classes": ["person"],
        "enabled": True
    })
    assert new_zone["id"] is not None
    assert new_zone["name"] == "Test Zone"

    # Update zone
    updated = store.update_zone(new_zone["id"], {"name": "Updated Zone Name"})
    assert updated["name"] == "Updated Zone Name"

    # Get zone
    fetched = store.get_zone(new_zone["id"])
    assert fetched["name"] == "Updated Zone Name"

    # Delete zone
    deleted = store.delete_zone(new_zone["id"])
    assert deleted is True
    assert store.get_zone(new_zone["id"]) is None
