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
