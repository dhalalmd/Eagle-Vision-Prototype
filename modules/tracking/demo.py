import argparse
import time
import cv2
import numpy as np
from shared.schemas import FrameContext, Detection, ObjectClass
from modules.tracking.module import Module

def main():
    parser = argparse.ArgumentParser(description="M02 Tracking Standalone Demo")
    parser.add_argument("--source", type=str, default="data/samples/border.mp4", help="Video file or camera index")
    args = parser.parse_args()

    tracker_mod = Module({"enabled": True})
    tracker_mod.setup()

    # Try loading detector for real video demo; fallback to synthetic if not available
    detector_mod = None
    try:
        from modules.detection.module import Module as DetectionModule
        detector_mod = DetectionModule({"enabled": True, "conf": 0.4})
        detector_mod.setup()
        print("Loaded detection module for demo.")
    except Exception as e:
        print(f"Detection module setup skipped ({e}); running with synthetic moving detections.")

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)

    frame_id = 0
    syn_x = 100
    syn_dir = 5

    print("Running tracking demo... Press 'q' to quit.")
    while True:
        if cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            time.sleep(0.04)

        frame_id += 1
        ctx = FrameContext(camera_id="cam1", frame_id=frame_id, timestamp=time.time(), frame=frame)

        if detector_mod:
            detector_mod.process(ctx)
        else:
            # Synthetic moving person detection
            syn_x += syn_dir
            if syn_x > 500 or syn_x < 50:
                syn_dir *= -1
            ctx.detections = [
                Detection(bbox=(syn_x, 150, syn_x + 60, 300), cls=ObjectClass.PERSON, conf=0.92)
            ]

        t0 = time.time()
        tracker_mod.process(ctx)
        dt = time.time() - t0
        fps = 1.0 / dt if dt > 0 else 0

        for trk in ctx.tracks:
            x1, y1, x2, y2 = trk.bbox
            color = (0, 255, 0) if trk.cls == ObjectClass.PERSON else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"#{trk.track_id} {trk.cls.value}", (x1, max(y1 - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.putText(frame, f"FPS: {fps:.1f} | Active Tracks: {len(ctx.tracks)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("M02 Tracking Demo", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    tracker_mod.teardown()
    if detector_mod:
        detector_mod.teardown()

if __name__ == "__main__":
    main()
