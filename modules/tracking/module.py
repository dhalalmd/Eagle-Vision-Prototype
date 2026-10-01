from typing import Dict
from modules.base import BaseModule
from shared.schemas import FrameContext
from modules.tracking.tracker import ByteTracker
from shared.logger import logger

class Module(BaseModule):
    name = "tracking"
    stage = "ana"
    order = 40
    requires = ("detection",)

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.trackers: Dict[str, ByteTracker] = {}
        self.track_thresh = float(self.cfg.get("track_thresh", 0.3))
        self.low_thresh = float(self.cfg.get("low_thresh", 0.1))
        self.max_time_lost = int(self.cfg.get("max_time_lost", 30))

    def setup(self) -> None:
        self.trackers.clear()
        logger.info("Tracking module initialized (ByteTrack)")

    def process(self, ctx: FrameContext) -> None:
        if not ctx.camera_id:
            return

        # Get or create tracker for camera
        if ctx.camera_id not in self.trackers:
            self.trackers[ctx.camera_id] = ByteTracker(
                track_thresh=self.track_thresh,
                low_thresh=self.low_thresh,
                max_time_lost=self.max_time_lost
            )

        tracker = self.trackers[ctx.camera_id]
        ctx.tracks = tracker.update(ctx.detections)

    def teardown(self) -> None:
        self.trackers.clear()
