import pytest
import time
from shared.schemas import FrameContext, Track, ObjectClass, EventType, Severity
from shared.zone_store import ZoneStore
from modules.intrusion.module import Module as IntrusionModule
from tests.fixtures import make_ctx, fake_track

def test_intrusion_entry_fires_once_and_cooldown(tmp_path):
    zones_file = tmp_path / "zones.json"
    zstore = ZoneStore(file_path=zones_file)
    for z in zstore.list_zones():
        zstore.delete_zone(z["id"])

    zstore.add_zone({
        "id": "z1",
        "camera_id": "cam1",
        "name": "Border line",
        "points": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        "classes": ["person", "vehicle"],
        "enabled": True
    })

    import modules.intrusion.module as int_mod
    orig_store = int_mod.zone_store
    int_mod.zone_store = zstore

    try:
        mod = IntrusionModule({"enabled": True, "cooldown_s": 10.0})
        mod.setup()

        # Track inside zone (center = (320, 240) in 640x480 frame)
        trk = fake_track(track_id=3, bbox=(300, 200, 340, 240), cls=ObjectClass.PERSON, label="person")
        t0 = 1000.0
        ctx1 = make_ctx(camera_id="cam1", frame_id=1, tracks=[trk], ts=t0)

        mod.process(ctx1)

        assert len(ctx1.events) == 1
        evt = ctx1.events[0]
        assert evt.type == EventType.INTRUSION
        assert evt.severity == Severity.HIGH
        assert evt.track_id == 3
        assert evt.zone_id == "z1"
        assert 'Person #3 entered zone "Border line"' in evt.message
        assert evt.meta["label"] == "person"
        assert evt.meta["zone_name"] == "Border line"

        # Second frame within cooldown (5s later)
        ctx2 = make_ctx(camera_id="cam1", frame_id=2, tracks=[trk], ts=t0 + 5.0)
        mod.process(ctx2)
        assert len(ctx2.events) == 0

        # Third frame after cooldown (11s later)
        ctx3 = make_ctx(camera_id="cam1", frame_id=3, tracks=[trk], ts=t0 + 11.0)
        mod.process(ctx3)
        assert len(ctx3.events) == 1

        mod.teardown()
    finally:
        int_mod.zone_store = orig_store

def test_intrusion_animal_ignored(tmp_path):
    zones_file = tmp_path / "zones.json"
    zstore = ZoneStore(file_path=zones_file)
    for z in zstore.list_zones():
        zstore.delete_zone(z["id"])

    zstore.add_zone({
        "id": "z_test",
        "camera_id": "cam1",
        "name": "Border line",
        "points": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        "classes": ["person", "vehicle"],
        "enabled": True
    })

    import modules.intrusion.module as int_mod
    orig_store = int_mod.zone_store
    int_mod.zone_store = zstore

    try:
        mod = IntrusionModule({"enabled": True, "cooldown_s": 10.0})
        mod.setup()

        # Dog track inside zone
        dog_trk = fake_track(track_id=10, bbox=(300, 200, 340, 240), cls=ObjectClass.ANIMAL, label="dog")
        ctx1 = make_ctx(camera_id="cam1", frame_id=1, tracks=[dog_trk], ts=1000.0)

        mod.process(ctx1)
        assert len(ctx1.events) == 0  # Animal ignored by default

        # Now enable "animal" in zone classes
        zstore.update_zone("z_test", {"classes": ["person", "vehicle", "animal"]})

        ctx2 = make_ctx(camera_id="cam1", frame_id=2, tracks=[dog_trk], ts=1000.0)
        mod.process(ctx2)
        assert len(ctx2.events) == 1
        assert ctx2.events[0].track_id == 10

        mod.teardown()
    finally:
        int_mod.zone_store = orig_store
