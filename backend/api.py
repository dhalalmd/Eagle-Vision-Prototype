import socket
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Optional
import yaml
from pathlib import Path

from backend.models import CameraCreate, CameraUpdate, SystemInfo
from core.camera_manager import CameraManager
from core.streamer import generate_mjpeg_stream
from core.registry import ModuleRegistry
from core.pipeline import Pipeline
from shared.logger import logger

router = APIRouter()

# Global instances set during app initialization
camera_manager: Optional[CameraManager] = None
module_registry: Optional[ModuleRegistry] = None
pipeline: Optional[Pipeline] = None

def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@router.get("/cameras")
def list_cameras():
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    return camera_manager.list_cameras()

@router.post("/cameras")
def add_camera(payload: CameraCreate):
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    return camera_manager.add_camera(
        name=payload.name,
        cam_type=payload.type,
        source=payload.source,
        enabled=payload.enabled
    )

@router.patch("/cameras/{cam_id}")
def update_camera(cam_id: str, payload: CameraUpdate):
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    updated = camera_manager.update_camera(
        cam_id=cam_id,
        name=payload.name,
        source=payload.source,
        enabled=payload.enabled,
        settings=payload.settings
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Camera not found")
    return updated

@router.delete("/cameras/{cam_id}")
def delete_camera(cam_id: str):
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    success = camera_manager.delete_camera(cam_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"status": "deleted", "id": cam_id}

@router.post("/cameras/{cam_id}/reset-settings")
def reset_camera_settings(cam_id: str):
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    result = camera_manager.reset_settings(cam_id)
    if not result:
        raise HTTPException(status_code=404, detail="Camera not found")
    return result

@router.get("/webcams")
def get_webcams():
    return CameraManager.probe_webcams()

@router.get("/system/info", response_model=SystemInfo)
def get_system_info():
    return SystemInfo(
        lan_ip=get_lan_ip(),
        http_port=8000,
        https_port=8443
    )

@router.get("/stream/{cam_id}")
def stream_mjpeg(cam_id: str):
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    cam = camera_manager.get_camera(cam_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    return StreamingResponse(
        generate_mjpeg_stream(camera_manager, cam_id, pipeline=pipeline),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/modules")
def list_modules():
    if not module_registry:
        return []
    return module_registry.list_modules_info()

@router.post("/modules/{name}/toggle")
def toggle_module(name: str):
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="config.yaml not found")
    
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    modules_cfg = cfg.get("modules", {})
    if name not in modules_cfg:
        modules_cfg[name] = {"enabled": True}
    else:
        current = modules_cfg[name].get("enabled", False)
        modules_cfg[name]["enabled"] = not current

    cfg["modules"] = modules_cfg
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)

    if module_registry:
        module_registry.load_modules()

    return {"name": name, "enabled": modules_cfg[name]["enabled"]}

@router.post("/modules/{name}/config")
def update_module_config(name: str, payload: dict):
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise HTTPException(status_code=404, detail="config.yaml not found")
    
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    modules_cfg = cfg.get("modules", {})
    if name not in modules_cfg:
        modules_cfg[name] = {}
    
    modules_cfg[name].update(payload)
    cfg["modules"] = modules_cfg
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)

    if module_registry:
        module_registry.load_modules()

    return {"name": name, "config": modules_cfg[name]}

import csv
import io
import time
from fastapi.responses import StreamingResponse, Response, FileResponse
from backend.models import CameraCreate, CameraUpdate, SystemInfo, ZoneCreate, ZoneUpdate, AlertUpdate
from shared.zone_store import zone_store
from shared.alert_store import alert_store

@router.get("/zones")
def list_zones(camera_id: Optional[str] = None):
    return zone_store.list_zones(camera_id=camera_id)

@router.post("/zones")
def create_zone(payload: ZoneCreate):
    return zone_store.add_zone(payload.dict())

@router.patch("/zones/{zone_id}")
def update_zone(zone_id: str, payload: ZoneUpdate):
    data = payload.dict(exclude_unset=True)
    updated = zone_store.update_zone(zone_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Zone not found")
    return updated

@router.delete("/zones/{zone_id}")
def delete_zone(zone_id: str):
    success = zone_store.delete_zone(zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Zone not found")
    return {"status": "deleted", "id": zone_id}

@router.get("/alerts")
def list_alerts(
    camera_id: Optional[str] = None,
    type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    date_from: Optional[float] = None,
    date_to: Optional[float] = None,
    limit: int = 50,
    offset: int = 0
):
    items, total = alert_store.list_alerts(
        camera_id=camera_id, type=type, severity=severity, status=status,
        q=q, date_from=date_from, date_to=date_to, limit=limit, offset=offset
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.get("/alerts/stats")
def get_alerts_stats():
    return alert_store.get_stats()

@router.get("/alerts/export.csv")
def export_alerts_csv(
    camera_id: Optional[str] = None,
    type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    date_from: Optional[float] = None,
    date_to: Optional[float] = None
):
    items, _ = alert_store.list_alerts(
        camera_id=camera_id, type=type, severity=severity, status=status,
        q=q, date_from=date_from, date_to=date_to, limit=10000, offset=0
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Time", "Camera", "Type", "Severity", "Title", "Message", "Status", "Remarks", "Evidence Path"])

    for a in items:
        dt_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a.get("timestamp", 0)))
        writer.writerow([
            a.get("id"),
            dt_str,
            a.get("camera_id"),
            a.get("type"),
            a.get("severity"),
            a.get("title"),
            a.get("message"),
            a.get("status"),
            a.get("remarks"),
            a.get("evidence_path") or ""
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alerts.csv"}
    )

@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int):
    alert = alert_store.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: int, payload: AlertUpdate):
    updated = alert_store.update_alert(alert_id, status=payload.status, remarks=payload.remarks)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    return updated

@router.get("/evidence/{path:path}")
def get_evidence(path: str):
    full_path = Path("data/evidence") / path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Evidence file not found")
    return FileResponse(str(full_path))
