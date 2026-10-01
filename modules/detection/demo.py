import argparse
import time
import cv2
import numpy as np
from pathlib import Path
from shared.schemas import FrameContext
from modules.detection.module import Module

def main():
    parser = argparse.ArgumentParser(description="M01 Detection Standalone Demo")
    parser.add_argument("--source", type=str, default="data/samples/border.mp4", help="Video file or camera index")
    args = parser.parse_args()

    cfg = {"enabled": True, "model": "yolov8n.pt", "conf": 0.4, "imgsz": 480, "device": "auto"}
    detector = Module(cfg)
    print("Setting up detector...")
    detector.setup()

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Error: Could not open video source '{args.source}'")
        return

    frame_id = 0
    print("Running detection demo... Press 'q' to quit.")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_id += 1
        ctx = FrameContext(camera_id="cam1", frame_id=frame_id, timestamp=time.time(), frame=frame)
        
        t0 = time.time()
        detector.process(ctx)
        dt = time.time() - t0

        fps = 1.0 / dt if dt > 0 else 0
        
        for det in ctx.detections:
            x1, y1, x2, y2 = det.bbox
            color = (0, 255, 0) if det.cls == "person" else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"{det.cls.value} {det.conf:.2f}", (x1, max(y1 - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.putText(frame, f"FPS: {fps:.1f} | Detections: {len(ctx.detections)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("M01 Detection Demo", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.teardown()

if __name__ == "__main__":
    main()
