import time
from shared.schemas import FrameContext, Event, EventType, Severity
from modules.alerts.module import Module as AlertsModule
from shared.alert_store import alert_store

def main():
    print("Running Alerts Module Demo...")
    mod = AlertsModule({"enabled": True, "retention_days": 30})
    mod.setup()

    event = Event(
        type=EventType.INTRUSION,
        severity=Severity.HIGH,
        camera_id="cam1",
        timestamp=time.time(),
        frame_id=101,
        message='Person #5 entered zone "Front Line" on Laptop webcam',
        track_id=5,
        zone_id="z1",
        meta={"label": "person", "zone_name": "Front Line", "camera_name": "Laptop webcam"}
    )

    ctx = FrameContext(
        camera_id="cam1",
        frame_id=101,
        timestamp=time.time(),
        frame=None,
        events=[event]
    )

    mod.process(ctx)
    print("Processed sample intrusion event into alert_store & log file.")

    alerts, total = alert_store.list_alerts(limit=5)
    print(f"Total alerts in store: {total}")
    for a in alerts:
        print(f" - [{a['id']}] {a['severity'].upper()} | {a['title']} | Status: {a['status']}")

    mod.teardown()

if __name__ == "__main__":
    main()
