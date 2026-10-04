import sqlite3
import json
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from shared.constants import DATA_DIR
from shared.logger import logger

ALERTS_DB = Path(DATA_DIR) / "alerts.db"

class AlertStore:
    def __init__(self, db_path: Path = ALERTS_DB):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        camera_id TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        frame_id INTEGER NOT NULL,
                        message TEXT NOT NULL,
                        track_id INTEGER,
                        zone_id TEXT,
                        evidence_path TEXT,
                        meta TEXT,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'new',
                        acknowledged_at REAL,
                        remarks TEXT DEFAULT ''
                    )
                    """)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_cam ON alerts(camera_id)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(timestamp)")
            finally:
                conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        d = dict(row)
        if d.get("meta"):
            try:
                d["meta"] = json.loads(d["meta"])
            except Exception:
                d["meta"] = {}
        else:
            d["meta"] = {}
        return d

    def add_alert(self, data: dict) -> dict:
        with self._lock:
            conn = self._get_connection()
            try:
                meta_json = json.dumps(data.get("meta", {})) if isinstance(data.get("meta"), dict) else "{}"
                title = data.get("title") or f"{data.get('type', 'Alert').capitalize()} on {data.get('camera_id')}"
                now = time.time()
                ts = data.get("timestamp") or now
                status = data.get("status", "new")

                with conn:
                    cursor = conn.execute("""
                    INSERT INTO alerts (
                        type, severity, camera_id, timestamp, frame_id, message,
                        track_id, zone_id, evidence_path, meta, title, status, acknowledged_at, remarks
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(data.get("type", "intrusion")),
                        str(data.get("severity", "high")),
                        str(data.get("camera_id", "cam1")),
                        float(ts),
                        int(data.get("frame_id", 0)),
                        str(data.get("message", "")),
                        data.get("track_id"),
                        data.get("zone_id"),
                        data.get("evidence_path"),
                        meta_json,
                        title,
                        status,
                        data.get("acknowledged_at"),
                        data.get("remarks", "")
                    ))
                    new_id = cursor.lastrowid

                return self.get_alert(new_id) or {}
            finally:
                conn.close()

    def list_alerts(
        self,
        camera_id: Optional[str] = None,
        type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        date_from: Optional[float] = None,
        date_to: Optional[float] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[dict], int]:
        with self._lock:
            conn = self._get_connection()
            try:
                where_clauses = []
                params = []

                if camera_id and camera_id != "all":
                    where_clauses.append("camera_id = ?")
                    params.append(camera_id)

                if type and type != "all":
                    where_clauses.append("type = ?")
                    params.append(type)

                if severity and severity != "all":
                    where_clauses.append("severity = ?")
                    params.append(severity)

                if status and status != "all":
                    where_clauses.append("status = ?")
                    params.append(status)

                if date_from is not None:
                    where_clauses.append("timestamp >= ?")
                    params.append(float(date_from))

                if date_to is not None:
                    where_clauses.append("timestamp <= ?")
                    params.append(float(date_to))

                if q:
                    where_clauses.append("(message LIKE ? OR title LIKE ? OR remarks LIKE ?)")
                    wildcard = f"%{q}%"
                    params.extend([wildcard, wildcard, wildcard])

                where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

                # Count query
                count_query = f"SELECT COUNT(*) FROM alerts{where_sql}"
                cursor = conn.execute(count_query, params)
                total_count = cursor.fetchone()[0]

                # Select query
                select_query = f"SELECT * FROM alerts{where_sql} ORDER BY id DESC LIMIT ? OFFSET ?"
                select_params = params + [limit, offset]
                cursor = conn.execute(select_query, select_params)
                rows = cursor.fetchall()

                return [self._row_to_dict(row) for row in rows], total_count
            finally:
                conn.close()

    def get_alert(self, alert_id: int) -> Optional[dict]:
        with self._lock:
            conn = self._get_connection()
            try:
                cursor = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
                return None
            finally:
                conn.close()

    def update_alert(self, alert_id: int, status: Optional[str] = None, remarks: Optional[str] = None) -> Optional[dict]:
        with self._lock:
            conn = self._get_connection()
            try:
                updates = []
                params = []
                if status is not None:
                    updates.append("status = ?")
                    params.append(status)
                    if status in ("ack", "resolved"):
                        updates.append("acknowledged_at = ?")
                        params.append(time.time())

                if remarks is not None:
                    updates.append("remarks = ?")
                    params.append(remarks)

                if not updates:
                    return self.get_alert(alert_id)

                params.append(alert_id)
                update_sql = f"UPDATE alerts SET {', '.join(updates)} WHERE id = ?"
                with conn:
                    conn.execute(update_sql, params)

                return self.get_alert(alert_id)
            finally:
                conn.close()

    def get_stats(self) -> dict:
        with self._lock:
            conn = self._get_connection()
            try:
                total_cursor = conn.execute("SELECT COUNT(*) FROM alerts")
                total = total_cursor.fetchone()[0]

                unread_cursor = conn.execute("SELECT COUNT(*) FROM alerts WHERE status = 'new'")
                unread = unread_cursor.fetchone()[0]

                sev_cursor = conn.execute("SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
                by_sev = {row[0]: row[1] for row in sev_cursor.fetchall()}

                status_cursor = conn.execute("SELECT status, COUNT(*) FROM alerts GROUP BY status")
                by_status = {row[0]: row[1] for row in status_cursor.fetchall()}

                return {
                    "total": total,
                    "unread": unread,
                    "by_severity": by_sev,
                    "by_status": by_status
                }
            finally:
                conn.close()

    def delete_older_than(self, days: int) -> int:
        if days <= 0:
            return 0
        cutoff = time.time() - (days * 86400)
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute("DELETE FROM alerts WHERE timestamp < ?", (cutoff,))
                    deleted = cursor.rowcount
                return deleted
            finally:
                conn.close()

# Global instance
alert_store = AlertStore()
