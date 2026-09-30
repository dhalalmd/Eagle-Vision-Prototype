from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Optional
from shared.logger import logger
from core.camera_manager import CameraManager

router = APIRouter()

camera_manager: Optional[CameraManager] = None

class AlertConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending alert websocket message: {e}")

alert_manager = AlertConnectionManager()

@router.websocket("/ws/phone/{camera_id}")
async def phone_websocket(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    logger.info(f"Phone WebSocket connected for camera {camera_id}")
    
    if camera_manager:
        cam = camera_manager.get_camera(camera_id)
        if not cam:
            # Auto register phone camera
            camera_manager.add_camera(
                name=f"Phone ({camera_id})",
                cam_type="phone",
                source="",
                enabled=True,
                cam_id=camera_id
            )

    try:
        while True:
            data = await websocket.receive_bytes()
            if camera_manager:
                reader = camera_manager.get_reader(camera_id)
                if reader:
                    reader.push_jpeg(data)
    except WebSocketDisconnect:
        logger.info(f"Phone WebSocket disconnected for camera {camera_id}")
    except Exception as e:
        logger.error(f"Error in phone websocket for camera {camera_id}: {e}")

@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await alert_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_manager.disconnect(websocket)
