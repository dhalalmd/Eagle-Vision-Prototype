import pytest
from tests.fixtures import make_ctx
from shared.schemas import ObjectClass

def test_detection_module_initialization():
    from modules.detection.module import Module
    mod = Module({"enabled": True, "conf": 0.5, "imgsz": 480})
    assert mod.name == "detection"
    assert mod.stage == "ana"
    assert mod.order == 30
    assert mod.conf == 0.5

def test_detection_process_with_missing_model():
    from modules.detection.module import Module
    mod = Module({"enabled": True})
    ctx = make_ctx()
    mod.process(ctx)
    assert ctx.detections == []

def test_detection_setup_and_predict():
    from modules.detection.module import Module
    mod = Module({"enabled": True, "conf": 0.4, "device": "cpu"})
    try:
        mod.setup()
    except Exception:
        pytest.skip("YOLO weights or ultralytics model not available locally for test")
    
    ctx = make_ctx()
    mod.process(ctx)
    assert isinstance(ctx.detections, list)
    mod.teardown()
