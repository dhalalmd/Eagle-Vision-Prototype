from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CameraCreate(BaseModel):
    name: str
    type: str = Field(..., description="webcam | phone | url | file")
    source: str = ""
    enabled: bool = True

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    source: Optional[str] = None
    enabled: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None

class SystemInfo(BaseModel):
    lan_ip: str
    http_port: int = 8000
    https_port: int = 8443

class ZoneCreate(BaseModel):
    camera_id: str = "cam1"
    name: str
    points: List[List[float]]
    classes: List[str] = Field(default_factory=lambda: ["person", "vehicle"])
    enabled: bool = True

class ZoneUpdate(BaseModel):
    camera_id: Optional[str] = None
    name: Optional[str] = None
    points: Optional[List[List[float]]] = None
    classes: Optional[List[str]] = None
    enabled: Optional[bool] = None

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    remarks: Optional[str] = None
