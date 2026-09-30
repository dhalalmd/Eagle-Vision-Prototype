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
from shared.logger import logger

router = APIRouter()

# Global instances set during app initialization
camera_manager: Optional[CameraManager] = None
module_registry: Optional[ModuleRegistry] = None

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
        enabled=payload.enabled
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
        generate_mjpeg_stream(camera_manager, cam_id),
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

@router.get("/zones")
def get_zones():
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            intrusion_cfg = cfg.get("modules", {}).get("intrusion", {})
            return intrusion_cfg.get("zones", [])
    return []

@router.get("/events")
def list_events(camera_id: Optional[str] = None, type: Optional[str] = None, severity: Optional[str] = None, limit: int = 50):
    return []

@router.get("/events/{event_id}")
def get_event(event_id: str):
    raise HTTPException(status_code=404, detail="Event not found")

@router.get("/evidence/{path:path}")
def get_evidence(path: str):
    raise HTTPException(status_code=404, detail="Evidence not found")
