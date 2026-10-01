# M02 Tracking Module

Performs multi-object tracking using ByteTrack on per-camera streams.

## Config Keys
- `enabled`: `true` / `false`
- `track_thresh`: Detection score threshold for tracking (default: `0.3`)
- `low_thresh`: Low detection score threshold for ByteTrack second stage (default: `0.1`)
- `max_time_lost`: Frames to remember lost tracks (default: `30`)

## Inputs / Outputs
- Reads: `ctx.detections`
- Writes: `ctx.tracks`

## Run Standalone Demo
```bash
python -m modules.tracking.demo --source data/samples/border.mp4
```
