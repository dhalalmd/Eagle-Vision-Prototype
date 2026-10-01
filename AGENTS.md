# AGENTS.md — SIH26187 Smart Border CCTV

Rules for **every AI agent and team member**. Read fully before writing any code.
If something here conflicts with your own habits, **this file wins**. If unsure, ask the user.

---

## 0. START HERE — how this file is used

**AGENTS.md and PROGRESS.md live in the project root and are the master copies.** Your tool may load AGENTS.md automatically; **you must read PROGRESS.md yourself at the start of every session. Never ask the user to upload either file.** Only if neither file is in the folder (fresh folder or new platform) will the user attach them once: save both into the project root. The user then gives you **one task**, for example:
- "Build M00 core"
- "Build module M11 loitering"
- "Fix intrusion" / "Improve detection speed"
- "Integrate module anpr into main"

Do exactly that task, nothing more. Your steps:

1. Read AGENTS.md and PROGRESS.md fully.
2. Find the module in section 4 (ID, stage, order, requires, tech) and section 10 (details).
3. Check the target folder. If `shared/`, `modules/base.py`, `tests/fixtures.py` are missing, create them **verbatim** from sections 5 and 14. If they exist, do not edit them.
4. Build only: `modules/<name>/` (`module.py`, `demo.py`, `requirements.txt`, `README.md`), `tests/test_<name>.py`, and the `config.yaml` block. If the module's `requires` are not present, use mocks (section 14). Do not build the required modules.
5. Write **complete, runnable files**. No placeholders, no "rest of code here", no pseudo-code, no TODO stubs.
6. Do not ask questions unless the task is impossible. State assumptions in one line and proceed.
7. **Keep the docs current, automatically. Never wait to be asked.** Every time the user gives a new instruction, requirement, preference, bug report or decision (any message, any platform):
   - add a dated one-line row to **section 17** of AGENTS.md, and edit the relevant section too if it changes how things must be built;
   - update **PROGRESS.md** (module status, change log, decisions, open issues).
   A change the user asks for counts as approved, including contract changes: also add a line to `docs/CONTRACT_CHANGELOG.md`. Edit both files **in place in the project root** (do not only print them) and include them in your commit. Never delete old rows; mark them `superseded`. If you truly have no file access, print the exact lines for the user to paste.
8. Finish with the **Delivery report** (section 14), including the `DOCS UPDATED:` line.

Sections 9 and 12 mention git. If there is no git repo in your folder, skip the git steps and still deliver everything else.

---

## 1. Project in one line

Software-only AI layer on existing CCTV: RTSP in → detect → track → analyse → alert/evidence → dashboard.
Prototype for Smart India Hackathon. Runs on Windows, Linux and macOS.

## 2. Architecture: modular plug-in pipeline

- `core/` = pipeline loop + module registry + ingest. Knows nothing about features.
- Every feature is a **module** in `modules/<name>/` and plugs into the pipeline.
- Modules talk **only through `FrameContext`** (section 5). They never import each other.
- Each module can be enabled/disabled in `config.yaml` (or at runtime via API). Disabled = not imported, not installed, no errors.
- A crashing module must **never** crash the pipeline (section 7).

```
Ingest → [preprocess modules] → detection → tracking → [analyse modules]
       → [output modules: event_engine → evidence → database → alerts → emergency_trigger]
       → streamer (draws overlay, publishes to dashboard)
```

## 3. Folder structure (do not rename)

```
AGENTS.md  PROGRESS.md  config.yaml  .env.example  docker-compose.yml  requirements.txt
shared/     schemas.py  constants.py  config.py  logger.py     <- SHARED CONTRACT
core/       ingest.py  camera_manager.py  image_adjust.py  pipeline.py  registry.py  streamer.py
modules/    base.py  <name>/module.py  <name>/demo.py  <name>/requirements.txt
backend/    main.py  api.py  ws.py  db.py  models.py  static/phone.html
frontend/   (React + Tailwind)
tests/      fixtures.py  test_<name>.py
data/       samples/  evidence/  cameras.json   <- git-ignored
scripts/    gen_cert.py  run_dev.py
docs/
```

Rule: **folder name = config key = `Module.name` = module ID name** (e.g. `intrusion`).

## 4. Module list

Phases: **P0** core → **P1** MVP → **P2** secondary → **P3** future (do NOT build yet).
Stages: `pre` (preprocess), `ana` (analyse), `out` (output). Lower `order` runs first.

| ID | name | Phase | Stage | Order | Requires | Tech | Owner |
|---|---|---|---|---|---|---|---|
| M00 | core (ingest, camera manager, pipeline, live view, camera management UI) | P0 | — | — | — | OpenCV, FFmpeg, FastAPI, React | |
| M01 | detection | P1 | ana | 30 | — | YOLOv8 | |
| M02 | tracking | P1 | ana | 40 | detection | ByteTrack | |
| M03 | intrusion | P1 | ana | 50 | tracking | Shapely | |
| M04 | event_engine | P1 | out | 200 | — | Python, Redis (optional) | |
| M05 | evidence | P1 | out | 210 | event_engine | OpenCV, FFmpeg | |
| M06 | database | P1 | out | 220 | event_engine | PostgreSQL / SQLite | |
| M07 | alerts | P1 | out | 230 | event_engine | FastAPI WebSocket | |
| M08 | dashboard (events, alerts, toggles, zones) | P1 | — | — | M00 | React + Tailwind | |
| M09 | tamper | P2 | pre | 10 | — | frame-diff, blur | |
| M10 | night_enhance | P2 | pre | 20 | — | CLAHE, gamma | |
| M11 | loitering | P2 | ana | 60 | tracking | dwell-time counter | |
| M12 | object_left | P2 | ana | 70 | tracking | MOG2 | |
| M13 | anpr | P2 | ana | 80 | detection | YOLOv8 plate + PaddleOCR/EasyOCR | |
| M14 | emergency_trigger | P2 | out | 240 | event_engine | Twilio (**simulated only**) | |
| M15 | reid (multi-camera) | P3 | ana | 90 | tracking | OSNet/torchreid | |
| M16 | face (recognition) | P3 | ana | 100 | detection | RetinaFace + InsightFace | |
| M17 | anomaly (predictive) | P3 | ana | 110 | tracking | TBD | |
| M18 | responsible_ai (audit log, access control, retention) | P2 | — | — | database | backend | |

Build order: M00 → M01 → M02 → M03 → M04 → M05 → M06 → M07 → M08 → P2 modules.
**Never start a module before its `Requires` are working.** Never build P3 unless told.

## 5. SHARED CONTRACT — single source of truth

Create these files **exactly** as below. Do not rename, reorder or remove any field/name.
Need a change the user did not ask for? **Stop and ask the user.** If the user asked for it or approved it, edit here and in `shared/` together and add a line to `docs/CONTRACT_CHANGELOG.md`.

### shared/schemas.py
```python
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional
import numpy as np

class ObjectClass(str, Enum):
    PERSON = "person"
    VEHICLE = "vehicle"

class EventType(str, Enum):
    INTRUSION = "intrusion"
    LOITERING = "loitering"
    OBJECT_LEFT = "object_left"
    TAMPER = "tamper"
    ANPR = "anpr"
    REID_MATCH = "reid_match"
    FACE_MATCH = "face_match"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Detection:
    bbox: tuple[int, int, int, int]      # x1, y1, x2, y2 in PIXELS
    cls: ObjectClass
    conf: float                          # 0.0 - 1.0

@dataclass
class Track:
    track_id: int
    bbox: tuple[int, int, int, int]      # x1, y1, x2, y2 in PIXELS
    cls: ObjectClass
    conf: float

    @property
    def bottom_center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, y2)

@dataclass
class Event:
    type: EventType
    severity: Severity
    camera_id: str
    timestamp: float                     # epoch seconds (time.time())
    frame_id: int
    message: str = ""
    track_id: Optional[int] = None
    zone_id: Optional[str] = None
    evidence_path: Optional[str] = None  # set by evidence module
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class FrameContext:
    camera_id: str
    frame_id: int
    timestamp: float
    frame: np.ndarray                    # BGR (OpenCV order)
    detections: list[Detection] = field(default_factory=list)
    tracks: list[Track] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)   # extras[module_name] = output
```

### shared/constants.py
```python
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}
VEHICLE_COCO_IDS = {2, 3, 5, 7}   # car, motorcycle, bus, truck
PERSON_COCO_ID = 0
DATA_DIR = "data"
EVIDENCE_DIR = "data/evidence"
```

### modules/base.py
```python
from abc import ABC, abstractmethod
from shared.schemas import FrameContext

class BaseModule(ABC):
    name: str = ""                       # == folder name == config key
    stage: str = ""                      # "pre" | "ana" | "out"
    order: int = 0
    requires: tuple[str, ...] = ()       # names of modules that must be enabled

    def __init__(self, cfg: dict):
        self.cfg = cfg                   # this module's block from config.yaml

    def setup(self) -> None:             # heavy imports + model loading go HERE
        pass

    @abstractmethod
    def process(self, ctx: FrameContext) -> None:   # mutate ctx in place, return None
        ...

    def teardown(self) -> None:
        pass
```

### Module file rules
- `modules/<name>/module.py` must define a class named exactly `Module(BaseModule)`.
- `registry.py` auto-discovers modules by folder name. No manual registration.
- Read config with defaults: `self.cfg.get("conf", 0.4)` — never `self.cfg["conf"]`.
- **Lazy imports:** import heavy libs (torch, ultralytics, paddleocr, torchreid, insightface) **inside `setup()`**, never at file top.
- Heavy extra dependencies go in `modules/<name>/requirements.txt`, not the root file.

### Data rules (who writes what)
| Field | Written by | Read by |
|---|---|---|
| `ctx.frame` | ingest; `night_enhance` may replace it | everyone |
| `ctx.detections` | `detection` only | tracking, anpr, face |
| `ctx.tracks` | `tracking` only | all analyse modules |
| `ctx.events` | analyse modules **append** only | event_engine and outputs |
| `ctx.extras[name]` | the module named `name` only | dashboard/outputs |

- Modules **never draw** on `ctx.frame`. Overlay (boxes, zones, labels) is drawn by `core/streamer.py`.
- Modules **never** write to another module's fields.

### Units and formats (everyone, always)
- Boxes: pixel `xyxy`. Colour order: **BGR**. Time: epoch seconds float.
- Zones in config: polygon points **normalised 0–1** (resolution independent). Convert to pixels inside the module.
- IDs: `camera_id` is a string like `"cam1"`; `zone_id` is a string; `track_id` is an int.
- Names: `snake_case` for files/functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants.
- Never invent new event types, severities or class names. Use the enums.

### extras output shapes
| Module | `ctx.extras[...]` |
|---|---|
| `tamper` | `{"tampered": bool, "reason": "blur"|"static"|"blocked"|None}` |
| `night_enhance` | `{"applied": bool}` |
| `anpr` | `[{"track_id": int, "plate": str, "conf": float}]` |
| `loitering` | `{track_id: dwell_seconds}` |
| `object_left` | `[{"bbox": (x1,y1,x2,y2), "age_s": float}]` |
| `reid` | `[{"track_id": int, "global_id": str, "score": float}]` |

## 6. config.yaml (source of truth for on/off and settings)

```yaml
cameras:          # SEED ONLY: copied once into data/cameras.json; after that cameras.json is the source of truth
  - {id: cam1, name: "Laptop webcam", type: webcam, source: "0", enabled: true}
modules:
  detection:   {enabled: true,  model: yolov8n.pt, conf: 0.4, device: auto, frame_skip: 0}
  tracking:    {enabled: true}
  intrusion:   {enabled: true,  cooldown_s: 10,
                zones: [{id: z1, name: "Border line", points: [[0.1,0.6],[0.9,0.6],[0.9,0.9],[0.1,0.9]]}]}
  event_engine: {enabled: true, cooldown_s: 10, use_redis: false}
  evidence:    {enabled: true,  pre_s: 5, post_s: 5}
  database:    {enabled: true,  url: "sqlite:///data/events.db"}
  alerts:      {enabled: true}
  tamper:      {enabled: false}
  night_enhance: {enabled: false, brightness_threshold: 60}
  loitering:   {enabled: false, dwell_s: 30}
  object_left: {enabled: false, static_s: 60}
  anpr:        {enabled: false}
  emergency_trigger: {enabled: false, simulate: true}
```

- Secrets (Twilio keys, DB password, RTSP password) go in `.env` only. Keep `.env.example` updated.
- Defaults that work with **no GPU, no Redis, no Postgres** must always exist (`device: auto` falls back to CPU, `use_redis: false` uses in-memory, SQLite for dev).

## 7. Error safety (so one module never breaks the app)

- `pipeline.py` wraps **every** `module.process(ctx)` in try/except: log the error with module name + frame_id, continue.
- After 5 consecutive failures a module is auto-disabled and flagged in `/api/modules`.
- If a module in `requires` is disabled, the dependent module is skipped with a warning (no crash).
- Ingest must auto-reconnect on stream drop (retry with backoff), never exit.
- Use `pathlib.Path`, never hardcoded `C:\` or `/home/...` paths, never OS-specific shell commands.
- Use the logger from `shared/logger.py`, not `print`.

## 8. Backend API contract (frontend and backend must match exactly)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/cameras` | list cameras (camera record below, with live fields) |
| POST | `/api/cameras` | add `{name, type, source, enabled}` → returns record (id auto-assigned: cam1, cam2…) |
| PATCH | `/api/cameras/{id}` | edit `name`, `source`, `enabled`, `settings` (partial; server clamps to the ranges below) |
| DELETE | `/api/cameras/{id}` | remove; stops its worker and releases the device |
| POST | `/api/cameras/{id}/reset-settings` | reset `settings` to defaults |
| GET | `/api/webcams` | local webcam indexes available `[{index, name}]` (probe 0–4, skip ones in use) |
| GET | `/api/system/info` | `{lan_ip, http_port, https_port}` |
| WS | `/ws/phone/{camera_id}` | phone pushes binary JPEG frames. Text messages: phone→server `off` (camera paused), `ping:<ms>`; server→phone `pong:<ms>` |
| GET | `/phone?cam={camera_id}` | phone capture page (static HTML) |
| GET | `/api/stream/{camera_id}` | MJPEG live stream (annotated) |
| WS | `/ws/alerts` | pushes `Event.to_dict()` JSON per alert |
| GET | `/api/events?camera_id=&type=&severity=&limit=50` | event history |
| GET | `/api/events/{id}` | one event + evidence path |
| GET | `/api/evidence/{path}` | serve screenshot/clip |
| GET | `/api/modules` | `[{name, enabled, status, failures}]` |
| POST | `/api/modules/{name}/toggle` | enable/disable at runtime |
| GET/POST | `/api/zones` | read/save fence polygons (normalised) |

Camera record (JSON, exact keys):
```json
{"id": "cam1", "name": "Laptop webcam", "type": "webcam", "source": "0", "enabled": true,
 "settings": {"brightness": 0, "contrast": 1.0, "saturation": 1.0, "zoom": 1.0, "rotate": 0,
              "flip_h": false, "flip_v": false, "grayscale": false, "invert_colors": false},
 "status": "online", "fps": 24.5, "last_frame_age_ms": 40, "note": ""}
```
- `type`: `webcam` | `phone` | `url` | `file`. `source`: webcam → device index as string; phone → `""` (frames are pushed); url → `rtsp://` or `http://` MJPEG URL (e.g. "IP Webcam" phone app); file → path (loops).
- `status`: `online` | `connecting` | `offline` | `error`. Stored fields: `id, name, type, source, enabled, settings`. Live fields (`status, fps, last_frame_age_ms, note`) are computed, never stored. `note` is a short reason, e.g. `"paused by phone"`.
- `settings` (all optional in PATCH; unknown keys ignored; values clamped):

| key | type | range | default | effect |
|---|---|---|---|---|
| `brightness` | int | -100..100 | 0 | added to pixel values |
| `contrast` | float | 0.5..2.0 | 1.0 | multiplier |
| `saturation` | float | 0.0..2.0 | 1.0 | colour strength |
| `zoom` | float | 1.0..3.0 | 1.0 | centre crop, scaled back up |
| `rotate` | int | 0, 90, 180, 270 | 0 | clockwise |
| `flip_h` | bool | | false | mirror left-right |
| `flip_v` | bool | | false | flip upside-down |
| `grayscale` | bool | | false | black and white |
| `invert_colors` | bool | | false | colour negative |

- Applied **server-side in the camera worker, right after reading the frame and before `FrameContext` is built**, so the dashboard stream and all modules see the same adjusted image. Order: rotate → flip → zoom → brightness/contrast → saturation → grayscale → invert. Skip every step that is at its default (zero cost when untouched). Use a LUT for brightness/contrast.
- Until M06 exists, cameras persist in `data/cameras.json`.

DB tables (from M06): `events` (mirrors `Event` fields), `zones`, `cameras`, `audit_log` (who, action, time).
Alert WebSocket message = exactly `Event.to_dict()`. Do not change key names.

## 9. Module workflow (one module at a time)

1. `git pull`, read `PROGRESS.md`, pick **one** module whose `Requires` are done.
2. `git switch -c feat/<module_name>`
3. Touch **only**: `modules/<name>/`, your block in `config.yaml`, `tests/test_<name>.py`. Anything else needs user approval.
4. Provide `modules/<name>/demo.py` so the module runs standalone on a sample video:
   `python -m modules.<name>.demo --source data/samples/border.mp4`
5. Write `tests/test_<name>.py` using a fake `FrameContext` (no camera needed).
6. **Definition of done:**
   - Demo runs with module on, and app still runs with module **off**
   - Test passes
   - Works on CPU
   - No changes to `shared/`
   - Does not slow the pipeline below 10 FPS on the sample video (note results in `PROGRESS.md`)
7. `git commit`, `git push`, tell the user to review and merge. Append to `PROGRESS.md`: date, agent, module, what changed, what's next.

Integration test: `python -m core.pipeline --only detection,tracking,intrusion` runs just those modules.

## 10. Module details

**M00 core** — Four camera types: `webcam` (OpenCV index; `CAP_DSHOW` on Windows, default backend elsewhere), `url` (RTSP/HTTP), `file` (loops), `phone` (browser pushes frames).
- `core/camera_manager.py`: `CameraManager` with `add`, `remove`, `update`, `list`, `get_latest_jpeg`. One worker thread per camera. Persists to `data/cameras.json` (seeded from `config.yaml` once). Add/remove work at runtime without restart; `remove` stops the thread and releases the device.
- `pipeline.py`: per-camera loop builds `FrameContext`, runs enabled modules. **Must work with zero modules.**
- `streamer.py`: keeps the newest JPEG per camera; MJPEG endpoint serves it.
- `image_adjust.py`: `apply_settings(frame, settings) -> frame` (section 8 table). Called by the camera worker.

*Low-latency rules (mandatory):*
1. Reader thread keeps **only the latest frame** (no queue, no backlog). Set `CAP_PROP_BUFFERSIZE=1`.
2. Stream max 640 px wide, JPEG quality 70, target 25 FPS. Encode JPEG once per frame, share across viewers.
3. MJPEG generator sends only a frame newer than the last one sent. It never buffers.
4. A slow module or slow viewer must never block a reader. Drop frames, never queue them.
5. `online` if a frame arrived within 3 s, else `offline`. Auto-reconnect with backoff.

*Phone camera:* browsers allow camera access only on HTTPS (or localhost). Backend serves HTTP `8000` and HTTPS `8443` (self-signed cert from `scripts/gen_cert.py`, pure Python, cross-platform, includes the LAN IP). Phone opens `https://<lan_ip>:8443/phone?cam=<id>` and accepts the certificate warning once. `backend/static/phone.html` is plain HTML+JS (no framework), mobile-first, dark, and **looks like a camera app**:
- Full-screen live preview. Top bar: camera name, red **LIVE** badge with timer, connection dot. Bottom control row like a camera app.
- Big round **start/stop** button (red while live) = camera **ON/OFF**. OFF stops and releases the camera track (phone camera light goes off), sends text `off`, and the preview shows "Camera off". The dashboard tile shows `offline` with note `paused by phone`. ON restarts the stream.
- Buttons: switch front/back, torch (only if supported), snapshot (saves a JPEG to the phone), grid lines, mirror preview (preview only), hide UI / fullscreen, settings.
- Settings sheet: resolution (320x240 / **640x480 default** / 1280x720), FPS (15 / **24** / 30), JPEG quality (30-90%, default 60), zoom slider (if supported), keep screen on (default on).
- Stats line: FPS sent, ping ms (via `ping:`/`pong:`), connection status.
- Remember settings in `localStorage` (inside try/catch). Defaults must stay low-lag.
- Always: `canvas.toBlob('image/jpeg', q)`, binary WebSocket to `/ws/phone/{id}`, skip a frame if `ws.bufferedAmount` > 100 KB, Screen Wake Lock, auto-reconnect with backoff, `facingMode` front/back.

*Done when:* laptop webcam and phone camera are live on the dashboard **at the same time**, each ≥20 FPS, visible delay under ~300 ms on the same Wi-Fi; cameras can be added, edited, deleted at runtime and survive a restart; unplugging a source shows `offline` and it recovers on its own; image settings apply live and persist; layout 4 shows all cameras on one screen without scrolling.

**M01 detection** — YOLOv8n default. Map COCO ids to `ObjectClass` using `constants.py`. Writes `ctx.detections`. Config: `model, conf, device, frame_skip`.

**M02 tracking** — ByteTrack. Consumes `ctx.detections`, writes `ctx.tracks` with stable `track_id` per camera.

**M03 intrusion** — Shapely polygon from normalised zone points; test `track.bottom_center`. On entry append `Event(INTRUSION, HIGH, ...)` with `zone_id`, `track_id`. Fires once per track per zone per `cooldown_s`.

**M04 event_engine** — Dedups same `type+track_id+zone_id` within cooldown, adjusts severity (e.g. vehicle in zone → higher), drops low-confidence noise. Redis optional; falls back to in-memory dict.

**M05 evidence** — Screenshot at event + rolling clip (`pre_s` before, `post_s` after) saved to `data/evidence/<camera_id>/<timestamp>_<type>.jpg|mp4`. Sets `event.evidence_path`.

**M06 database** — SQLAlchemy. Inserts every event. SQLite default, PostgreSQL via `DATABASE_URL`.

**M07 alerts** — Broadcasts each event over `/ws/alerts`.

**M08 dashboard** — Dark command-center theme. Sidebar: Live, Cameras, Events*, Modules*, Settings* (*placeholder pages until built). Top bar: clock, cameras online x/y, system status. Right panel: live alerts feed (empty placeholder until M07).
- *Live page:* layout buttons **1 / 2 / 4 / 9 / auto**; the chosen layout is remembered (`localStorage`). The grid must **fill the visible area with no page scroll**: height `calc(100vh - topbar)`, CSS grid `repeat(cols,1fr)` x `repeat(rows,1fr)`, video `object-fit: contain`. Meaning: `1` = 1x1, `2` = 2x1 side by side, `4` = 2x2, `9` = 3x3, `auto` = best fit for **all** cameras (cols = ceil(sqrt(n))). If cameras > cells, show prev/next buttons and "page x/y". Unused cells show a faint "No camera" slot. Example: 3 cameras on layout 4 → all 3 visible together in a 2x2 grid.
- Tile = `<img src="/api/stream/{id}">` + name, status dot, FPS, and the `note` when offline. Click = fullscreen, Esc exits. Offline tile shows a placeholder and retries.
- *Cameras page:* cards or table with status, enable toggle, edit, delete (confirm). **Add camera** modal with a type picker: Laptop webcam (dropdown from `/api/webcams`), Phone camera (after saving, shows a QR code + link for `/phone?cam=<id>`), IP/RTSP URL, Video file.
- *Edit camera modal:* name, source, enabled, plus **Image settings** (section 8 table): sliders for brightness, contrast, saturation, zoom; toggles for flip horizontal, flip vertical, grayscale, invert colours; rotate buttons (0/90/180/270); **Reset** button. Shows a **live preview** beside the controls. Changes apply instantly (`PATCH` with partial `settings`, debounced ~150 ms) and persist. Cancel restores the values from when the modal opened.
- Polls `/api/cameras` every 2 s. Vite dev proxy forwards `/api` and `/ws` to the backend. Later pages: Event history, Modules toggles, Zone editor, Evidence viewer.

**M09 tamper** — Frame-diff, Laplacian blur score, static-frame check. Writes `extras["tamper"]`; appends `TAMPER` event. Runs first (order 10).

**M10 night_enhance** — If mean brightness < threshold, apply CLAHE + gamma to `ctx.frame`. Runs before detection.

**M11 loitering** — Per track dwell-time inside a zone; event when `dwell_s` exceeded. Zone-specific thresholds.

**M12 object_left** — MOG2 background subtraction; a static blob older than `static_s` with no person nearby → `OBJECT_LEFT`.

**M13 anpr** — Plate detector on vehicle crops + OCR. Writes `extras["anpr"]`; appends `ANPR` event.

**M14 emergency_trigger** — On `CRITICAL` events, **simulate** a Twilio call (log + dashboard banner). Never wire real dispatch.

**M15–M17** — Future scope. Do not build.

**M18 responsible_ai** — Audit log for every login/toggle/zone change, retention limit (auto-delete evidence older than N days), role-based access on API. No real personal data in the repo.

## 11. Code style

- Short, simple, readable. No over-engineering. Minimal comments, only where logic is not obvious.
- Small functions, one job each. Type hints on public functions.
- Add a dependency only if needed; put it in the right requirements file.
- Do not reformat or rewrite files you were not asked to change. Do not delete files without asking.

## 12. Git rules

- Branch per module: `feat/<module_name>`; fixes: `fix/<thing>`.
- Commit often: `type: message` (`feat`, `fix`, `docs`, `refactor`, `chore`). Example: `feat: add intrusion zone check`.
- Never commit `.env`, `*.pt`, videos, `data/evidence/`, `node_modules/`, `__pycache__/`.
- Always `git pull` before starting; commit before ending your session so the next AI starts clean.
- Never `git push --force`.

## 13. Hard limits

- No new event types, severities, or shared fields without approval.
- No P3 work. No real emergency calls.
- No feature outside the current module's scope.
- If you hit an error caused by another module or by `shared/`, **do not patch it yourself** — report it to the user.

---

## 14. Standalone mode (building a module on its own) + Delivery report

Modules may be built separately, on different AI platforms or folders, then merged later. This works because every module only needs `shared/` + `modules/base.py` + a `FrameContext`.

### tests/fixtures.py (create verbatim if missing)
```python
import time
import numpy as np
from shared.schemas import FrameContext, Track, Detection, ObjectClass

def make_ctx(camera_id="cam1", frame_id=0, frame=None, tracks=None,
             detections=None, ts=None):
    if frame is None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
    return FrameContext(
        camera_id=camera_id, frame_id=frame_id,
        timestamp=ts if ts is not None else time.time(),
        frame=frame, detections=detections or [], tracks=tracks or [])

def fake_track(track_id=1, bbox=(100, 100, 200, 300),
               cls=ObjectClass.PERSON, conf=0.9):
    return Track(track_id=track_id, bbox=bbox, cls=cls, conf=conf)

def fake_detection(bbox=(100, 100, 200, 300), cls=ObjectClass.PERSON, conf=0.9):
    return Detection(bbox=bbox, cls=cls, conf=conf)
```

### Rules for standalone work
- **Missing dependency module?** Mock its output with `make_ctx(tracks=[fake_track(...)])` or `fake_detection(...)`. Never build or edit other modules.
- `demo.py` must run with **no other module installed**: read a video (`--source`, default `data/samples/border.mp4`), build a `FrameContext` per frame, run `Module.process`, print events and FPS, and optionally show the frame with OpenCV.
- `test_<name>.py` must use only `tests/fixtures.py` (no camera, no network, no GPU).
- Import only from `shared/`, `modules/base.py`, and standard/third-party libs. Never from `core/`, `backend/` or other modules.
- Keep module code path-independent (`pathlib`), so the folder can be dropped into the main repo unchanged.
- `README.md` inside the module folder: max 10 lines — what it does, config keys, inputs, outputs, run command.

### Delivery report (end of every task, in this exact format)

```
MODULE: <ID> <name>        STATUS: DONE | PARTIAL | BLOCKED
FILES:  <list of every file created/changed, with path>
CONFIG: <the config.yaml block to paste under `modules:`>
DEPS:   <pip packages to install, or "none">
RUN:    python -m modules.<name>.demo --source data/samples/border.mp4
TEST:   python -m pytest tests/test_<name>.py
INPUTS: <ctx fields read>      OUTPUTS: <ctx fields written / event types>
ASSUMPTIONS: <one line each, or "none">
KNOWN ISSUES: <or "none">
DOCS UPDATED: <AGENTS.md section 17 rows + PROGRESS.md rows added or changed>
PROGRESS ROW: | YYYY-MM-DD | <agent> | <name> | <what changed> | <what's next> |
```

If you have file access, also append the PROGRESS ROW to `PROGRESS.md` and update the module's status in the table. If not, output it for the user to paste.

---

## 15. Integrating a separately built module into main

For tasks like "Integrate module X". Steps:

1. Copy `modules/<name>/` and `tests/test_<name>.py` into the main repo.
2. Paste the module's `CONFIG` block into `config.yaml` (start with `enabled: false`).
3. Merge its `requirements.txt` into the module folder's own requirements (do not bloat the root file).
4. Run `python -m pytest tests/test_<name>.py`, then `python -m modules.<name>.demo`.
5. Set `enabled: true`, run `python -m core.pipeline --only <requires...>,<name>`.
6. Run the full pipeline with the module on, then off. Both must run clean.
7. If names or fields don't match `shared/`, **fix the module**, never `shared/`. If `shared/` itself seems wrong, report to the user.
8. Update `PROGRESS.md`: status `DONE`, tick "Merged to main" in the merge table.

## 16. Output rules for free-tier AI platforms (limited output/context)

- Deliver **file by file**, each complete, with its path as a heading above the code block.
- Keep each file under ~200 lines; split into helpers if longer.
- If you run out of space, stop at a file boundary and end with `NEXT: <next file to write>`. The user will say "continue".
- Do not refactor, rename, or "improve" anything outside the task.
- Do not repeat this file's contents back to the user.
- Prefer the simplest working solution. Short, readable code over clever code.

---

## 17. Requirements log (user instructions)

AI: when the user gives a new instruction, add a row here **automatically** (section 0, step 7). Never delete rows; mark old ones `superseded`.
Status: `Open` · `Done` · `superseded`.

| ID | Date | Instruction (short) | Status | Where |
|---|---|---|---|---|
| R01 | 2026-09-30 | Modular build: core first, then one feature at a time, each testable and toggleable | Done | Sections 2, 9 |
| R02 | 2026-09-30 | Modules may be built on other platforms/folders; user uploads AGENTS.md + PROGRESS.md and names a module | Done | Sections 0, 14, 15 |
| R03 | 2026-10-01 | Laptop webcam + phone cameras live on the dashboard at the same time, no lag; dashboard can add/delete/manage cameras | Done (tested: laptop + 2 phones) | M00, M08 |
| R04 | 2026-10-01 | Live page: layout 4 must show all cameras on one screen (was stuck on 2 columns) | Open | M08 Live page |
| R05 | 2026-10-01 | Camera edit options: brightness, contrast etc. plus invert/flip | Open | Section 8 `settings`, M08 Edit modal |
| R06 | 2026-10-01 | Phone page must feel like a camera app: camera ON/OFF button and more features | Open | M00 phone page |
| R07 | 2026-10-01 | AI must update AGENTS.md (new instructions) and PROGRESS.md automatically on any platform, without being told | Done | Section 0, step 7 |
| R08 | 2026-10-01 | Keep code short, simple and easy to read | Done | Section 11 |
| R09 | 2026-10-01 | No re-uploading AGENTS.md/PROGRESS.md each time: they live in the project root, the AI reads PROGRESS.md itself at session start and updates both files itself | Done | Section 0 |
