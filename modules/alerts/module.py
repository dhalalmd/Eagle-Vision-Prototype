import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from modules.base import BaseModule
from shared.schemas import FrameContext
from shared.alert_store import alert_store
from shared.constants import DATA_DIR
from shared.logger import logger

LOGS_DIR = Path(DATA_DIR) / "logs"

class Module(BaseModule):
    name = "alerts"
    stage = "out"
    order = 220
    requires = ()

    def __init__(self, cfg: dict):
        super().__init__(cfg)
        self.retention_days = int(self.cfg.get("retention_days", 30))
        self.last_cleanup_ts = 0.0

    def setup(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self._cleanup_old_records()
        logger.info(f"Alerts output module initialized (retention: {self.retention_days} days)")

    def _cleanup_old_records(self) -> None:
        now = time.time()
        # Clean SQLite alert records
        deleted_count = alert_store.delete_older_than(self.retention_days)
        if deleted_count > 0:
            logger.info(f"Alerts retention cleanup: deleted {deleted_count} alerts older than {self.retention_days} days")

        # Clean old log files in data/logs/
        if LOGS_DIR.exists():
            cutoff_sec = now - (self.retention_days * 86400)
            for f in LOGS_DIR.glob("alerts-*.log"):
                try:
                    if f.stat().st_mtime < cutoff_sec:
                        f.unlink()
                        logger.info(f"Alerts log retention cleanup: removed {f.name}")
                except Exception as e:
                    logger.error(f"Error cleaning old alert log file {f}: {e}")

        self.last_cleanup_ts = now

    def _build_alert_title(self, event) -> str:
        evt_type = str(event.type.value if hasattr(event.type, "value") else event.type).capitalize()
        label = event.meta.get("label", "target")
        track_str = f" #{event.track_id}" if event.track_id else ""
        zone_name = event.meta.get("zone_name") or event.zone_id
        if zone_name:
            return f'{evt_type}: {label}{track_str} in "{zone_name}"'
        return f"{evt_type}: {label}{track_str}"

    def process(self, ctx: FrameContext) -> None:
        # Check daily retention cleanup (once every 24 hours)
        now = time.time()
        if (now - self.last_cleanup_ts) >= 86400:
            self._cleanup_old_records()

        if not ctx.events:
            return

        dt_str = datetime.fromtimestamp(ctx.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        log_filename = f"alerts-{datetime.fromtimestamp(ctx.timestamp).strftime('%Y-%m-%d')}.log"
        log_path = LOGS_DIR / log_filename

        for event in ctx.events:
            try:
                title = self._build_alert_title(event)
                cam_name = event.meta.get("camera_name") or event.camera_id
                sev_str = str(event.severity.value if hasattr(event.severity, "value") else event.severity).upper()

                alert_dict = {
                    "type": str(event.type.value if hasattr(event.type, "value") else event.type),
                    "severity": str(event.severity.value if hasattr(event.severity, "value") else event.severity),
                    "camera_id": event.camera_id,
                    "timestamp": event.timestamp,
                    "frame_id": event.frame_id,
                    "message": event.message,
                    "track_id": event.track_id,
                    "zone_id": event.zone_id,
                    "evidence_path": event.evidence_path,
                    "meta": event.meta,
                    "title": title,
                    "status": "new",
                    "remarks": ""
                }

                # 1. Store in SQLite
                alert_store.add_alert(alert_dict)

                # 2. Append readable log line
                log_line = f"{dt_str} | {sev_str} | {cam_name} | {event.message}\n"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(log_line)

            except Exception as e:
                logger.error(f"Error processing alert event: {e}")

    def teardown(self) -> None:
        pass
