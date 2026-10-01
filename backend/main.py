import asyncio
import ssl
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

import backend.api as api_module
import backend.ws as ws_module
from core.camera_manager import CameraManager
from core.registry import ModuleRegistry
from core.pipeline import Pipeline
from shared.logger import logger
from scripts.gen_cert import generate_self_signed_cert

app = FastAPI(title="Smart Border CCTV API", version="1.0.0")

# Enable CORS for Vite dev server & dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API & WebSocket routers
app.include_router(api_module.router, prefix="/api")
app.include_router(ws_module.router)

# Initialize core managers & pipeline
camera_manager = CameraManager()
module_registry = ModuleRegistry()
pipeline = Pipeline(camera_manager, module_registry)

api_module.camera_manager = camera_manager
api_module.module_registry = module_registry
api_module.pipeline = pipeline
ws_module.camera_manager = camera_manager

@app.on_event("startup")
def startup_event():
    pipeline.start()
    logger.info("Pipeline started on application startup.")

@app.get("/phone", response_class=HTMLResponse)
def get_phone_page(cam: str = "cam_phone"):
    html_path = Path("backend/static/phone.html")
    if not html_path.exists():
        return HTMLResponse("<h1>phone.html not found</h1>", status_code=404)
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Stopping pipeline and camera manager readers...")
    pipeline.stop()
    for cam_id in list(camera_manager.readers.keys()):
        camera_manager._stop_reader(cam_id)

def start_servers():
    cert_file, key_file = generate_self_signed_cert("certs")

    config_http = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    config_https = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8443,
        ssl_keyfile=str(key_file),
        ssl_certfile=str(cert_file),
        log_level="info"
    )

    server_http = uvicorn.Server(config_http)
    server_https = uvicorn.Server(config_https)

    async def run_both():
        await asyncio.gather(
            server_http.serve(),
            server_https.serve()
        )

    asyncio.run(run_both())

if __name__ == "__main__":
    start_servers()
