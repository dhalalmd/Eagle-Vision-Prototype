import pytest
from tests.fixtures import make_ctx, fake_detection
from shared.schemas import ObjectClass
from modules.tracking.module import Module

def test_tracking_module_initialization():
    mod = Module({"enabled": True, "track_thresh": 0.4})
    assert mod.name == "tracking"
    assert mod.stage == "ana"
    assert mod.order == 40
    assert mod.requires == ("detection",)

def test_tracking_with_moving_detections():
    mod = Module({"enabled": True, "track_thresh": 0.3})
    mod.setup()

    # Frame 1: Detection at (100, 100, 200, 300)
    det1 = fake_detection(bbox=(100, 100, 200, 300), cls=ObjectClass.PERSON, conf=0.9)
    ctx1 = make_ctx(camera_id="cam1", frame_id=1, detections=[det1])
    mod.process(ctx1)

    assert len(ctx1.tracks) == 1
    t1_id = ctx1.tracks[0].track_id
    assert ctx1.tracks[0].cls == ObjectClass.PERSON

    # Frame 2: Detection moves slightly to (105, 102, 205, 302)
    det2 = fake_detection(bbox=(105, 102, 205, 302), cls=ObjectClass.PERSON, conf=0.88)
    ctx2 = make_ctx(camera_id="cam1", frame_id=2, detections=[det2])
    mod.process(ctx2)

    assert len(ctx2.tracks) == 1
    # Track ID must stay stable!
    assert ctx2.tracks[0].track_id == t1_id

    # Frame 3: A second person appears at (400, 100, 500, 300)
    det3 = fake_detection(bbox=(108, 103, 208, 303), cls=ObjectClass.PERSON, conf=0.9)
    det4 = fake_detection(bbox=(400, 100, 500, 300), cls=ObjectClass.PERSON, conf=0.85)
    ctx3 = make_ctx(camera_id="cam1", frame_id=3, detections=[det3, det4])
    mod.process(ctx3)

    assert len(ctx3.tracks) == 2
    track_ids = [t.track_id for t in ctx3.tracks]
    assert t1_id in track_ids

    mod.teardown()
