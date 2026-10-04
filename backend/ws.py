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
        camera_manager.clear_note(camera_id)

    try:
        while True:
            msg = await websocket.receive()
            if "bytes" in msg and msg["bytes"]:
                # Binary JPEG frame from phone
                if camera_manager:
                    reader = camera_manager.get_reader(camera_id)
                    if reader:
                        reader.push_jpeg(msg["bytes"])
            elif "text" in msg and msg["text"]:
                text = msg["text"]
                if text == "off":
                    # Phone camera paused — stop pushing frames, set note
                    logger.info(f"Phone camera {camera_id} paused by phone")
                    if camera_manager:
                        camera_manager.set_note(camera_id, "paused by phone")
                elif text == "on":
                    # Phone camera resumed
                    logger.info(f"Phone camera {camera_id} resumed by phone")
                    if camera_manager:
                        camera_manager.clear_note(camera_id)
                elif text.startswith("ping:"):
                    # Respond with pong for latency measurement
                    try:
                        await websocket.send_text(f"pong:{text[5:]}")
                    except Exception:
                        pass
    except WebSocketDisconnect:
        logger.info(f"Phone WebSocket disconnected for camera {camera_id}")
        if camera_manager:
            camera_manager.set_note(camera_id, "phone disconnected")
    except Exception as e:
        logger.error(f"Error in phone websocket for camera {camera_id}: {e}")

import asyncio
from shared.alert_store import alert_store

@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await websocket.accept()
    logger.info("Alerts WebSocket connected")
    
    # On connect: send nothing old, record max current alert ID
    alerts, _ = alert_store.list_alerts(limit=1)
    last_id = alerts[0]["id"] if alerts else 0

    try:
        while True:
            await asyncio.sleep(0.5)
            # Fetch new alerts created after last_id
            new_alerts, _ = alert_store.list_alerts(limit=50)
            if new_alerts:
                # Filter alerts with id > last_id sorted ascending
                unseen = [a for a in new_alerts if a.get("id", 0) > last_id]
                unseen.sort(key=lambda x: x["id"])
                for alert in unseen:
                    await websocket.send_json(alert)
                    last_id = max(last_id, alert["id"])
    except WebSocketDisconnect:
        logger.info("Alerts WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in alerts websocket: {e}")
