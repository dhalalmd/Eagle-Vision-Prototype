import pytest
import time
from pathlib import Path
from datetime import datetime
from shared.schemas import Event, EventType, Severity
from shared.alert_store import AlertStore
from modules.alerts.module import Module as AlertsModule
from tests.fixtures import make_ctx

def test_alert_store_crud_and_filters(tmp_path):
    db_file = tmp_path / "alerts.db"
    store = AlertStore(db_path=db_file)

    # 1. Add alerts
    a1 = store.add_alert({
        "type": "intrusion", "severity": "high", "camera_id": "cam1",
        "timestamp": 1000.0, "frame_id": 1, "message": "Intrusion detected on cam1",
        "title": "Intrusion: person #1 in Border", "status": "new", "remarks": ""
    })
    a2 = store.add_alert({
        "type": "loitering", "severity": "medium", "camera_id": "cam2",
        "timestamp": 2000.0, "frame_id": 2, "message": "Loitering on cam2",
        "title": "Loitering: person #2 in Gate", "status": "ack", "remarks": "Checking"
    })
    a3 = store.add_alert({
        "type": "intrusion", "severity": "critical", "camera_id": "cam1",
        "timestamp": 3000.0, "frame_id": 3, "message": "Vehicle intrusion on cam1",
        "title": "Intrusion: vehicle #3 in Fence", "status": "resolved", "remarks": "Resolved by guard"
    })

    assert a1["id"] is not None
    assert store.get_alert(a1["id"])["title"] == "Intrusion: person #1 in Border"

    # 2. Filter by camera_id
    items, total = store.list_alerts(camera_id="cam1")
    assert total == 2
    assert all(a["camera_id"] == "cam1" for a in items)

    # 3. Filter by severity
    items, total = store.list_alerts(severity="high")
    assert total == 1
    assert items[0]["id"] == a1["id"]

    # 4. Filter by status
    items, total = store.list_alerts(status="ack")
    assert total == 1
    assert items[0]["id"] == a2["id"]

    # 5. Search filter (q)
    items, total = store.list_alerts(q="Vehicle")
    assert total == 1
    assert items[0]["id"] == a3["id"]

    # 6. Date range filter
    items, total = store.list_alerts(date_from=1500.0, date_to=2500.0)
    assert total == 1
    assert items[0]["id"] == a2["id"]

    # 7. Update status and remarks
    updated = store.update_alert(a1["id"], status="ack", remarks="Investigating")
    assert updated["status"] == "ack"
    assert updated["remarks"] == "Investigating"
    assert updated["acknowledged_at"] is not None

    # 8. Stats
    stats = store.get_stats()
    assert stats["total"] == 3
    assert stats["by_status"]["ack"] == 2

def test_alerts_module_process_and_log_format(tmp_path):
    db_file = tmp_path / "alerts.db"
    store = AlertStore(db_path=db_file)

    import modules.alerts.module as alerts_mod
    orig_store = alerts_mod.alert_store
    orig_logs_dir = alerts_mod.LOGS_DIR

    test_logs_dir = tmp_path / "logs"
    alerts_mod.alert_store = store
    alerts_mod.LOGS_DIR = test_logs_dir

    try:
        mod = AlertsModule({"enabled": True, "retention_days": 30})
        mod.setup()

        ts = 1700000000.0  # fixed timestamp
        evt = Event(
            type=EventType.INTRUSION,
            severity=Severity.HIGH,
            camera_id="cam1",
            timestamp=ts,
            frame_id=42,
            message='Person #3 entered zone "Border line" on Laptop webcam',
            track_id=3,
            zone_id="z1",
            meta={"label": "person", "zone_name": "Border line", "camera_name": "Laptop webcam"}
        )
        ctx = make_ctx(camera_id="cam1", frame_id=42, ts=ts)
        ctx.events.append(evt)

        mod.process(ctx)

        # Verify SQLite store
        items, total = store.list_alerts()
        assert total == 1
        assert items[0]["message"] == 'Person #3 entered zone "Border line" on Laptop webcam'
        assert items[0]["title"] == 'Intrusion: person #3 in "Border line"'

        # Verify Log line format
        dt_day = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        dt_full = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        log_file = test_logs_dir / f"alerts-{dt_day}.log"
        assert log_file.exists()

        log_content = log_file.read_text(encoding="utf-8")
        expected_line = f'{dt_full} | HIGH | Laptop webcam | Person #3 entered zone "Border line" on Laptop webcam'
        assert expected_line in log_content

        mod.teardown()
    finally:
        alerts_mod.alert_store = orig_store
        alerts_mod.LOGS_DIR = orig_logs_dir

def test_alerts_retention_cleanup(tmp_path):
    db_file = tmp_path / "alerts.db"
    store = AlertStore(db_path=db_file)

    old_ts = time.time() - (40 * 86400)  # 40 days old
    recent_ts = time.time() - (5 * 86400) # 5 days old

    store.add_alert({"type": "intrusion", "severity": "high", "camera_id": "cam1", "timestamp": old_ts, "frame_id": 1, "message": "Old alert", "title": "Old"})
    store.add_alert({"type": "intrusion", "severity": "high", "camera_id": "cam1", "timestamp": recent_ts, "frame_id": 2, "message": "Recent alert", "title": "Recent"})

    assert store.get_stats()["total"] == 2

    import modules.alerts.module as alerts_mod
    orig_store = alerts_mod.alert_store
    orig_logs_dir = alerts_mod.LOGS_DIR

    test_logs_dir = tmp_path / "logs"
    test_logs_dir.mkdir(parents=True, exist_ok=True)

    # Create an old log file and a recent log file
    old_log_file = test_logs_dir / "alerts-2020-01-01.log"
    old_log_file.write_text("old log line\n")
    # set mtime to 40 days ago
    import os
    os.utime(old_log_file, (old_ts, old_ts))

    recent_log_file = test_logs_dir / "alerts-2026-10-01.log"
    recent_log_file.write_text("recent log line\n")

    alerts_mod.alert_store = store
    alerts_mod.LOGS_DIR = test_logs_dir

    try:
        mod = AlertsModule({"enabled": True, "retention_days": 30})
        mod.setup()  # setup triggers cleanup

        assert store.get_stats()["total"] == 1
        items, _ = store.list_alerts()
        assert items[0]["message"] == "Recent alert"

        # Check log files cleanup
        assert not old_log_file.exists()
        assert recent_log_file.exists()

        mod.teardown()
    finally:
        alerts_mod.alert_store = orig_store
        alerts_mod.LOGS_DIR = orig_logs_dir
