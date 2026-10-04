import argparse
import time
import cv2
import numpy as np
from shared.schemas import FrameContext, Track, ObjectClass
from modules.intrusion.module import Module as IntrusionModule

def main():
    parser = argparse.ArgumentParser(description="Standalone Intrusion Module Demo")
    parser.add_argument("--source", type=str, default="data/samples/border.mp4", help="Video source path")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.source)
    if not cap.isOpened():
        print(f"Failed to open source: {args.source}")
        return

    mod = IntrusionModule({"enabled": True, "cooldown_s": 5})
    mod.setup()

    frame_id = 0
    print("Running Intrusion Demo... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_id += 1
        h, w = frame.shape[:2]

        # Simulate a moving track entering center zone
        sim_x = int(w * 0.2 + (frame_id * 5) % int(w * 0.6))
        sim_y = int(h * 0.7)
        track = Track(
            track_id=1,
            bbox=(sim_x - 20, sim_y - 60, sim_x + 20, sim_y),
            cls=ObjectClass.PERSON,
            conf=0.9,
            label="person"
        )

        ctx = FrameContext(
            camera_id="cam1",
            frame_id=frame_id,
            timestamp=time.time(),
            frame=frame,
            tracks=[track]
        )

        mod.process(ctx)

        # Draw simulated track
        cv2.rectangle(frame, (sim_x - 20, sim_y - 60), (sim_x + 20, sim_y), (0, 255, 0), 2)
        cv2.putText(frame, f"#1 person", (sim_x - 20, sim_y - 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        for event in ctx.events:
            print(f"[EVENT] {event.message}")
            cv2.putText(frame, f"ALERT: {event.message}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow("M03 Intrusion Demo", frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    mod.teardown()

if __name__ == "__main__":
    main()
