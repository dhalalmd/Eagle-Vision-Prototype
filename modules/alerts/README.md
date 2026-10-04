# Alerts Output Module

Stage: `out` | Order: 220 | Requires: None

## Description
Persists pipeline events into `data/alerts.db` (SQLite) and writes daily readable text logs to `data/logs/alerts-YYYY-MM-DD.log`. Automatically enforces retention cleanup for old records.

## Config
```yaml
modules:
  alerts:
    enabled: true
    retention_days: 30
```

## Demo Run
```bash
python -m modules.alerts.demo
```
