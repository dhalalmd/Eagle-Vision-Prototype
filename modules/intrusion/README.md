# Intrusion Detection Module (M03)

Stage: `ana` | Order: 50 | Requires: `tracking`

## Description
Monitors tracked objects entering configured polygonal zones on each camera.
Triggers `INTRUSION` events (severity `HIGH`) when an allowed object class enters a zone.

## Config
```yaml
modules:
  intrusion:
    enabled: true
    cooldown_s: 10
```

## Demo Run
```bash
python -m modules.intrusion.demo --source data/samples/border.mp4
```
