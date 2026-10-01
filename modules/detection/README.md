# M01 Detection Module

Performs object detection using YOLOv8n to detect persons and vehicles (car, motorcycle, bus, truck).

## Config Keys
- `enabled`: `true` / `false`
- `model`: Model filename (default: `yolov8n.pt`)
- `conf`: Confidence threshold (default: `0.4`)
- `imgsz`: Inference image size (default: `480`)
- `device`: Device target `auto`, `cpu`, or `cuda`

## Inputs / Outputs
- Reads: `ctx.frame`
- Writes: `ctx.detections`

## Run Standalone Demo
```bash
python -m modules.detection.demo --source data/samples/border.mp4
```
