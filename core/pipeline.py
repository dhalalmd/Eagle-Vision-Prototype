import time
import threading
from typing import Optional, Dict
from shared.schemas import FrameContext
from shared.logger import logger
from shared.config import load_config
from core.camera_manager import CameraManager
from core.registry import ModuleRegistry

class Pipeline:
    def __init__(self, camera_manager: CameraManager, registry: Optional[ModuleRegistry] = None, config_path: str = "config.yaml"):
        self.camera_manager = camera_manager
        self.registry = registry or ModuleRegistry(config_path)
        self.config_path = config_path
        self.running = False
        self.threads: Dict[str, threading.Thread] = {}
        self.latest_contexts: Dict[str, FrameContext] = {}
        self._frame_counters: Dict[str, int] = {}
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None

    def start(self):
        if self.running:
            return
        self.running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name="PipelineMonitor")
        self._monitor_thread.start()
        logger.info("Pipeline started with per-camera analysis threads.")

    def stop(self):
        self.running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
        with self._lock:
            for cam_id, thread in list(self.threads.items()):
                if thread.is_alive():
                    thread.join(timeout=1.0)
            self.threads.clear()
        logger.info("Pipeline stopped.")

    def get_latest_context(self, camera_id: str) -> Optional[FrameContext]:
        with self._lock:
            return self.latest_contexts.get(camera_id)

    def _monitor_loop(self):
        """Monitors active cameras and manages analysis worker threads."""
        while self.running:
            try:
                cams = self.camera_manager.list_cameras()
                active_cam_ids = {c["id"] for c in cams if c.get("enabled", True)}

                with self._lock:
                    # Remove dead threads
                    for cam_id in list(self.threads.keys()):
                        if not self.threads[cam_id].is_alive():
                            del self.threads[cam_id]

                    # Start thread for new active cameras
                    for cam_id in active_cam_ids:
                        if cam_id not in self.threads:
                            t = threading.Thread(
                                target=self._camera_analysis_loop,
                                args=(cam_id,),
                                daemon=True,
                                name=f"Analysis-{cam_id}"
                            )
                            self.threads[cam_id] = t
                            t.start()
            except Exception as e:
                logger.error(f"Error in pipeline monitor loop: {e}")

            time.sleep(1.0)

    def _camera_analysis_loop(self, camera_id: str):
        """Per-camera async analysis loop running on latest frame at configured rate."""
        logger.info(f"Started analysis loop for camera {camera_id}")
        last_processed_ts = 0.0

        while self.running:
            try:
                # Check target analysis FPS from config (default 8 FPS)
                cfg = load_config(self.config_path)
                max_fps = float(cfg.get("max_fps", 8.0))
                sleep_interval = 1.0 / max_fps if max_fps > 0 else 0.125

                reader = self.camera_manager.get_reader(camera_id)
                if reader and reader.is_online():
                    latest = reader.get_latest_frame()
                    if latest is not None:
                        frame, ts = latest
                        if ts > last_processed_ts:
                            last_processed_ts = ts
                            ctx = self._run_pipeline_on_frame(camera_id, frame, ts)
                            if ctx is not None:
                                with self._lock:
                                    self.latest_contexts[camera_id] = ctx
            except Exception as e:
                logger.error(f"Error in camera analysis loop ({camera_id}): {e}")

            time.sleep(sleep_interval)

    def _run_pipeline_on_frame(self, camera_id: str, frame, ts: float) -> Optional[FrameContext]:
        frame_id = self._frame_counters.get(camera_id, 0) + 1
        self._frame_counters[camera_id] = frame_id

        ctx = FrameContext(
            camera_id=camera_id,
            frame_id=frame_id,
            timestamp=ts,
            frame=frame
        )

        active_modules = self.registry.get_active_modules()
        active_names = [m.name for m in active_modules]

        for mod in active_modules:
            missing_reqs = [req for req in mod.requires if req not in active_names]
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

    def process_camera_frame(self, camera_id: str) -> Optional[FrameContext]:
        """Synchronous process call on latest frame (for testing)."""
        reader = self.camera_manager.get_reader(camera_id)
        if not reader or not reader.is_online():
            return None

        latest = reader.get_latest_frame()
        if latest is None:
            return None

        frame, ts = latest
        ctx = self._run_pipeline_on_frame(camera_id, frame, ts)
        if ctx is not None:
            with self._lock:
                self.latest_contexts[camera_id] = ctx
        return ctx
