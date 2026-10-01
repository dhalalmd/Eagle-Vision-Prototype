# PROGRESS.md — SIH26187 Smart Border CCTV

**Rule for all agents:** read this before starting; append a log entry before finishing.
Status: `TODO` · `WIP` · `DONE` · `BLOCKED`

---

## How to use (with AGENTS.md)

1. Upload **AGENTS.md + PROGRESS.md** to any AI platform.
2. Give one task: `Build module M11 loitering` (or `Build M00 core`, `Integrate anpr`, `Fix intrusion`).
3. The AI returns files + a **Delivery report**. Paste its `PROGRESS ROW` into the change log below and update the tables.
4. When a module is built on a different platform, copy its folder into the main repo and ask an AI to `Integrate <name>`.

## Separately built modules (merge tracker)

| Module | Built on (platform) | Location (folder/zip/link) | Tests pass | Merged to main | Enabled |
|---|---|---|---|---|---|
| | | | | | |

## Current focus

M00 core: laptop webcam + phone camera live on dashboard at the same time, with add/edit/delete camera management. Prompt: `prompts/M00_core_prompt.md` (upload with AGENTS.md + PROGRESS.md).

## Module status

| ID | Module | Phase | Status | Owner | Branch | Notes |
|---|---|---|---|---|---|---|
| M00 | core (ingest, camera manager, pipeline, live view) | P0 | DONE | Antigravity | feat/m00 | Ingest (webcam, url, file, phone), CameraManager, Pipeline, Streamer |
| M01 | detection | P1 | TODO | | | |
| M02 | tracking | P1 | TODO | | | |
| M03 | intrusion | P1 | TODO | | | |
| M04 | event_engine | P1 | TODO | | | |
| M05 | evidence | P1 | TODO | | | |
| M06 | database | P1 | TODO | | | |
| M07 | alerts | P1 | TODO | | | |
| M08 | dashboard | P1 | DONE | Antigravity | feat/m08 | Live layout (1/2/4/9/auto), Camera image settings modal, Phone camera app UI |
| M09 | tamper | P2 | TODO | | | |
| M10 | night_enhance | P2 | TODO | | | |
| M11 | loitering | P2 | TODO | | | |
| M12 | object_left | P2 | TODO | | | |
| M13 | anpr | P2 | TODO | | | |
| M14 | emergency_trigger | P2 | TODO | | | |
| M18 | responsible_ai | P2 | TODO | | | |
| M15-M17 | reid, face, anomaly | P3 | DO NOT BUILD | | | Future scope |

## Setup checklist

- [x] Project summary analysed (SIH26187)
- [x] `AGENTS.md` written (modular rules, shared contract, module list, API contract)
- [x] `PROGRESS.md` created
- [x] Git repo initialised + GitHub remote linked
- [x] `.gitignore` added (`.env`, `*.pt`, `*.mp4`, `data/evidence/`, `node_modules/`, `__pycache__/`)
- [x] Folder structure created (per AGENTS.md section 3)
- [x] `shared/schemas.py`, `shared/constants.py`, `modules/base.py` created exactly as in AGENTS.md
- [x] `config.yaml` + `.env.example` created
- [x] Sample video added to `data/samples/`

## Decisions

| Date | Decision |
|---|---|
| 2026-09-30 | Modular plug-in architecture: core pipeline first, then one module at a time, each testable and toggleable |
| 2026-09-30 | Modules communicate only via `FrameContext`; never import each other |
| 2026-09-30 | Build with multiple free-tier AIs (Freebuff, Antigravity, others) in the same folder, tracked with git/GitHub |
| 2026-09-30 | Pipeline modules are Python; dashboard is React + Tailwind (Streamlit/HTML fallback if no React skills) |
| 2026-09-30 | Emergency trigger stays simulated; P3 features not built for prototype |
| 2026-09-30 | Modules may be assigned to team members (Owner column above) |
| 2026-10-01 | Cameras are managed at runtime and stored in `data/cameras.json` (config.yaml is seed only); camera types: webcam, phone, url, file |
| 2026-10-01 | Phone camera = phone browser page pushing JPEG frames over WebSocket (HTTPS required); fallback: "IP Webcam" app as `url` camera |
| 2026-10-01 | Modules may be built separately on different platforms/folders: upload AGENTS.md + PROGRESS.md, name one module, AI builds it standalone with mocks, then it is merged into main |
| 2026-10-01 | Tasks B1, F1, F2 completed: Live page layout (1/2/4/9/auto + grid + paging + persistence), Camera image settings (clamping, reset endpoint, backend worker apply, frontend sliders/toggles/preview), Phone camera app UI (OFF/ON, torch/snapshot/grid/mirror/settings, websocket off/ping/pong, camera note) |

## Change log (newest first)

| Date | Agent/Person | Module | What changed | Next |
|---|---|---|---|---|
| 2026-10-01 | Antigravity | M00 / M08 | Fixed Live page layout (B1: 1/2/4/9/auto grid, pagination, localStorage), camera settings (F1: LUT brightness/contrast, clamp, reset API, Edit modal preview), phone camera app (F2: camera ON/OFF, torch, snapshot, grid, mirror, settings sheet, WebSocket off/ping/pong) | Build M01 Detection |
| 2026-10-01 | Antigravity | M00 / M08 | Built M00 Core (ingest, camera manager, pipeline, streamer, registry) + M08 Camera Management Dashboard (Vite + React + Tailwind + QR code) | Build M01 Detection |
| 2026-10-01 | Claude | docs | `AGENTS.md`: added camera contract (camera record, CRUD endpoints, `/api/webcams`, `/api/system/info`, `/ws/phone`, `/phone`), `camera_manager.py`, low-latency rules, phone-camera design (HTTPS + WebSocket), dashboard design. Created `prompts/M00_core_prompt.md` | Run the M00 prompt in Antigravity |
| 2026-10-01 | Claude | docs | `AGENTS.md`: added sections 0 (START HERE task protocol), 14 (standalone mode, test fixtures, Delivery report), 15 (integrating separately built modules), 16 (free-tier output rules). `PROGRESS.md`: added usage guide + merge tracker. Both files saved in `sih-docs/` | Create skeleton / build M00 core |
| 2026-09-30 | Claude | docs | Created `PROGRESS.md` | Initialise git repo, create skeleton |
| 2026-09-30 | Claude | docs | Rewrote `AGENTS.md` as modular version: 19 modules, shared contract code, config.yaml flags, error-safety rules, API contract, per-module workflow | Create skeleton files from AGENTS.md |
| 2026-09-30 | Claude | docs | First `AGENTS.md` draft (general rules, stack, git workflow) | Superseded by modular version |
| 2026-09-30 | Claude | analysis | Analysed project summary, documented pipeline workflow | — |

## Open issues / blockers

- None yet.

## Next steps

1. `git init`, add `.gitignore`, first commit, push to GitHub
2. Ask AI to create skeleton: folders, `shared/`, `modules/base.py`, `config.yaml`, M00 core
3. Verify M00: sample video plays on dashboard with FPS overlay
4. Then M01 detection → M02 tracking → M03 intrusion

## Log entry template (copy when finishing a session)

```
| YYYY-MM-DD | <agent/person> | <module> | <what changed> | <what's next> |
```
