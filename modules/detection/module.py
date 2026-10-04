import os
import time
from pathlib import Path
from typing import Optional, List, Union
import numpy as np

from modules.base import BaseModule
from shared.schemas import FrameContext, Detection, ObjectClass
from shared.constants import COCO_MAP, DATA_DIR, get_coco_group
from shared.logger import logger

MODELS_DIR = Path(DATA_DIR) / "models"

class Module(BaseModule):
    name = "detection"
    stage = "ana"
    order = 30
    requires = ()

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.model = None
        self.conf = float(self.cfg.get("conf", 0.35))
        self.imgsz = int(self.cfg.get("imgsz", 640))
        self.device_cfg = str(self.cfg.get("device", "auto")).lower()
        self.model_name = str(self.cfg.get("model", "yolov8n.pt"))
        self.classes = self.cfg.get("classes", "all")
        self.device = "cpu"
        self.total_frames = 0
        self.total_ms = 0.0
        self.avg_ms = 0.0

    def setup(self) -> None:
        """Lazy imports + load YOLOv8 model."""
        import torch
        from ultralytics import YOLO

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODELS_DIR / self.model_name

        if self.device_cfg == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = self.device_cfg

        logger.info(f"Loading YOLO model '{self.model_name}' on device '{self.device}'...")
        
        target = str(model_path) if model_path.exists() else self.model_name
        self.model = YOLO(target)
        
        # Ensure model weights end up in data/models
        if not model_path.exists():
            downloaded = Path(self.model_name)
            if downloaded.exists():
                try:
                    downloaded.rename(model_path)
                except Exception:
                    pass

    def _is_class_allowed(self, label_name: str, obj_cls: ObjectClass) -> bool:
        classes_cfg = self.cfg.get("classes", self.classes)
        if classes_cfg == "all" or classes_cfg == ["all"]:
            return True
        if isinstance(classes_cfg, (list, tuple)):
            allowed = [str(c).lower() for c in classes_cfg]
            if "all" in allowed:
                return True
            label_lower = label_name.lower()
            cls_lower = obj_cls.value.lower()
            return (label_lower in allowed or cls_lower in allowed)
        return True

    def process(self, ctx: FrameContext) -> None:
        if self.model is None or ctx.frame is None:
            return

        t0 = time.perf_counter()
        try:
            results = self.model.predict(
                source=ctx.frame,
                conf=self.conf,
                imgsz=self.imgsz,
                device=self.device,
                verbose=False
            )

            detections = []
            if results and len(results) > 0:
                boxes = results[0].boxes
                names = results[0].names if hasattr(results[0], "names") else {}
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())

                        if cls_id in COCO_MAP:
                            label_name, obj_cls = COCO_MAP[cls_id]
                        else:
                            label_name = names.get(cls_id, f"obj_{cls_id}")
                            obj_cls = get_coco_group(label_name)

                        if not self._is_class_allowed(label_name, obj_cls):
                            continue

                        detections.append(Detection(
                            bbox=(x1, y1, x2, y2),
                            cls=obj_cls,
                            conf=round(conf, 4),
                            label=label_name
                        ))

            ctx.detections = detections

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            self.total_frames += 1
            self.total_ms += elapsed_ms
            self.avg_ms = self.total_ms / self.total_frames

            ctx.extras["detection"] = {
                "avg_ms": round(self.avg_ms, 2),
                "last_ms": round(elapsed_ms, 2),
                "count": len(detections)
            }
        except Exception as e:
            logger.error(f"Error in detection process: {e}")
            raise e

    def teardown(self) -> None:
        self.model = None

