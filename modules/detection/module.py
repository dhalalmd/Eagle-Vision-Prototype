import os
from pathlib import Path
from typing import Optional
import numpy as np

from modules.base import BaseModule
from shared.schemas import FrameContext, Detection, ObjectClass
from shared.constants import PERSON_COCO_ID, VEHICLE_COCO_IDS, DATA_DIR
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
        self.conf = float(self.cfg.get("conf", 0.4))
        self.imgsz = int(self.cfg.get("imgsz", 480))
        self.device_cfg = str(self.cfg.get("device", "auto")).lower()
        self.model_name = str(self.cfg.get("model", "yolov8n.pt"))
        self.device = "cpu"

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

    def process(self, ctx: FrameContext) -> None:
        if self.model is None or ctx.frame is None:
            return

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
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())

                        if cls_id == PERSON_COCO_ID:
                            obj_cls = ObjectClass.PERSON
                        elif cls_id in VEHICLE_COCO_IDS:
                            obj_cls = ObjectClass.VEHICLE
                        else:
                            continue

                        detections.append(Detection(
                            bbox=(x1, y1, x2, y2),
                            cls=obj_cls,
                            conf=round(conf, 4)
                        ))

            ctx.detections = detections
        except Exception as e:
            logger.error(f"Error in detection process: {e}")
            raise e

    def teardown(self) -> None:
        self.model = None
