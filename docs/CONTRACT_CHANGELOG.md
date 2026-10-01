# CONTRACT_CHANGELOG.md

| Date | Change | Approved By | Description |
|---|---|---|---|
| 2026-10-01 | Async per-camera analysis in `core/pipeline.py` | User Request (Speed spec) | Added multi-threaded analysis loop per camera running on latest frame at 8 FPS max to keep live stream at full frame rate without blocking reader threads. |
| 2026-10-01 | Overlay rendering labels in `core/streamer.py` | User Request (Overlay spec) | Streamer renders `#<id> person` / `#<id> vehicle` when tracking is active, and plain `person` / `vehicle` when tracking is off. |
