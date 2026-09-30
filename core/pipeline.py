import time
import threading
from typing import Optional, Dict
from shared.schemas import FrameContext
from shared.logger import logger
from core.camera_manager import CameraManager
from core.registry import ModuleRegistry

class Pipeline:
    def __init__(self, camera_manager: CameraManager, registry: Optional[ModuleRegistry] = None):
        self.camera_manager = camera_manager
        self.registry = registry or ModuleRegistry()
        self.running = False
        self.threads: Dict[str, threading.Thread] = {}
        self._frame_counters: Dict[str, int] = {}

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def process_camera_frame(self, camera_id: str) -> Optional[FrameContext]:
        reader = self.camera_manager.get_reader(camera_id)
        if not reader or not reader.is_online():
            return None

        latest = reader.get_latest_frame()
        if latest is None:
            return None

        frame, ts = latest
        frame_id = self._frame_counters.get(camera_id, 0) + 1
        self._frame_counters[camera_id] = frame_id

        ctx = FrameContext(
            camera_id=camera_id,
            frame_id=frame_id,
            timestamp=ts,
            frame=frame
        )

        # Run modules
        active_modules = self.registry.get_active_modules()
        for mod in active_modules:
            # Check requirements
            missing_reqs = [req for req in mod.requires if req not in [m.name for m in active_modules]]
            if missing_reqs:
                logger.warning(f"Skipping module {mod.name}: missing required modules {missing_reqs}")
                continue

            try:
                mod.process(ctx)
                self.registry.record_success(mod.name)
            except Exception as e:
                logger.error(f"Error in module {mod.name} on frame {frame_id} (camera {camera_id}): {e}")
                self.registry.record_failure(mod.name)

        return ctx
