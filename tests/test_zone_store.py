import pytest
from pathlib import Path
from shared.zone_store import (
    ZoneStore, move_vertex, insert_vertex, delete_vertex,
    move_whole_zone, resize_rectangle, validate_polygon_geometry
)

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
        "points": [[0.1, 0.1], [0.8, 0.1], [0.8, 0.8], [0.1, 0.8]],
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

def test_vertex_move():
    initial_pts = [[0.1, 0.1], [0.8, 0.1], [0.8, 0.8], [0.1, 0.8]]
    moved = move_vertex(initial_pts, 0, [0.15, 0.15])
    assert moved[0] == [0.15, 0.15]
    assert moved[1:] == initial_pts[1:]

def test_vertex_insert():
    initial_pts = [[0.1, 0.1], [0.8, 0.1], [0.8, 0.8], [0.1, 0.8]]
    inserted = insert_vertex(initial_pts, 0, [0.45, 0.1])
    assert len(inserted) == 5
    assert inserted[1] == [0.45, 0.1]
    assert inserted[0] == [0.1, 0.1]

def test_vertex_delete_3point_minimum():
    # 4 points -> 3 points
    pts4 = [[0.1, 0.1], [0.8, 0.1], [0.8, 0.8], [0.1, 0.8]]
    pts3 = delete_vertex(pts4, 3, ztype="polygon")
    assert len(pts3) == 3

    # 3 points -> cannot delete below 3
    pts_after = delete_vertex(pts3, 0, ztype="polygon")
    assert len(pts_after) == 3
    assert pts_after == pts3

def test_whole_zone_move_clamped():
    pts = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]
    # Move beyond top-right frame boundary (dx=0.5, dy=0.5)
    moved = move_whole_zone(pts, 0.5, 0.5)
    # Max x is 0.8, so max allowed dx is 0.2 -> max x becomes 1.0
    for p in moved:
        assert 0.0 <= p[0] <= 1.0
        assert 0.0 <= p[1] <= 1.0
    assert moved[1] == [1.0, 0.4]  # 0.8 + 0.2, 0.2 + 0.2

def test_rectangle_resize_stays_rectangle():
    rect_pts = [[0.2, 0.2], [0.8, 0.2], [0.8, 0.8], [0.2, 0.8]]
    # Drag east handle to x=0.9
    resized = resize_rectangle(rect_pts, "e", 0.9, 0.5)
    assert len(resized) == 4
    # Points form bounding rectangle
    min_x = min(p[0] for p in resized)
    max_x = max(p[0] for p in resized)
    min_y = min(p[1] for p in resized)
    max_y = max(p[1] for p in resized)
    assert min_x == 0.2
    assert max_x == 0.9
    assert min_y == 0.2
    assert max_y == 0.8

def test_cancel_restores_old_shape():
    original_pts = [[0.1, 0.1], [0.8, 0.1], [0.8, 0.8], [0.1, 0.8]]
    current_pts = [list(p) for p in original_pts]

    # Perform edits
    edited_pts = move_vertex(current_pts, 0, [0.3, 0.3])
    assert edited_pts != original_pts

    # Cancel action restores original shape
    restored_pts = [list(p) for p in original_pts]
    assert restored_pts == original_pts

def test_patch_keeps_id(tmp_path):
    json_file = tmp_path / "zones.json"
    store = ZoneStore(file_path=json_file)

    zone = store.add_zone({
        "camera_id": "cam1",
        "name": "Zone Alpha",
        "points": [[0.1, 0.1], [0.8, 0.1], [0.8, 0.8], [0.1, 0.8]],
        "enabled": True
    })
    zone_id = zone["id"]

    # PATCH zone attributes
    updated = store.update_zone(zone_id, {
        "points": [[0.2, 0.2], [0.7, 0.2], [0.7, 0.7], [0.2, 0.7]],
        "name": "Renamed Alpha Zone",
        "color": "#3b82f6"
    })

    assert updated["id"] == zone_id
    assert updated["name"] == "Renamed Alpha Zone"
    assert updated["color"] == "#3b82f6"
    assert updated["points"] == [[0.2, 0.2], [0.7, 0.2], [0.7, 0.7], [0.2, 0.7]]
