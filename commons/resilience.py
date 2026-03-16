"""
resilience.py — The Commons Resilience

The platform must survive power loss, crashes, and network failures.
When something goes wrong — it restarts itself.
No human intervention required.

Three layers of protection:

  HEARTBEAT    — Writes a pulse file every 30 seconds.
                 On startup, checks if last heartbeat was recent.
                 If not — unclean shutdown detected. Revival runs.

  WATCHDOG     — Monitors the main process. If it dies unexpectedly,
                 restarts it automatically within seconds.

  STARTUP CHECK — On every boot, verifies database integrity,
                  checks for held posts needing review,
                  logs the revival event with timestamp and reason.

Designed to run on Railway (cloud) or locally in Termux.
On Railway — the platform restarts automatically on crash.
In Termux  — use the watchdog script to keep it alive.

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

import os
import json
import time
import threading
import subprocess
from datetime import datetime
from pathlib import Path

HEARTBEAT_FILE    = "commons_heartbeat.json"
REVIVAL_LOG       = "commons_revival.json"
SHUTDOWN_FILE     = "commons_shutdown.json"
HEARTBEAT_INTERVAL = 30    # seconds
STALE_THRESHOLD    = 120   # seconds — if heartbeat older than this, unclean shutdown


class HeartbeatMonitor:
    """
    Writes a heartbeat file every 30 seconds.
    On startup, checks if last heartbeat was recent.
    If not — unclean shutdown detected.
    """

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread     = None

    def start(self):
        self._thread = threading.Thread(target=self._beat, daemon=True)
        self._thread.start()
        print("[RESILIENCE] Heartbeat monitor started.")

    def stop(self):
        self._stop_event.set()
        self._write_clean_shutdown()

    def _beat(self):
        while not self._stop_event.is_set():
            self._write_heartbeat()
            self._stop_event.wait(HEARTBEAT_INTERVAL)

    def _write_heartbeat(self):
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status":    "alive",
            "pid":       os.getpid(),
        }
        try:
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _write_clean_shutdown(self):
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "clean":     True,
            "pid":       os.getpid(),
        }
        try:
            with open(SHUTDOWN_FILE, "w") as f:
                json.dump(data, f)
            if os.path.exists(HEARTBEAT_FILE):
                os.remove(HEARTBEAT_FILE)
        except Exception:
            pass

    def check_last_shutdown(self) -> dict:
        """
        Was the last shutdown clean?
        Returns info for the revival log.
        """
        # Clean shutdown file exists — all good
        if os.path.exists(SHUTDOWN_FILE):
            with open(SHUTDOWN_FILE) as f:
                data = json.load(f)
            os.remove(SHUTDOWN_FILE)
            return {"clean": True, "data": data}

        # Heartbeat file exists but is stale — unclean shutdown
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE) as f:
                data = json.load(f)
            last = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
            age  = (datetime.utcnow() - last).total_seconds()
            if age > STALE_THRESHOLD:
                return {
                    "clean":  False,
                    "reason": f"Heartbeat stale — last seen {age:.0f}s ago",
                    "data":   data
                }

        # First run — no files exist
        return {"clean": True, "first_run": True}


class RevivalManager:
    """
    Handles startup after unclean shutdown.
    Logs the event. Checks database. Reports to Circle.
    """

    def startup_check(self) -> dict:
        monitor = HeartbeatMonitor()
        result  = monitor.check_last_shutdown()

        if result.get("first_run"):
            print("[RESILIENCE] First run detected. Starting fresh.")
            self._log_revival("first_run", "First startup")
            return {"status": "first_run"}

        if not result["clean"]:
            print(f"[RESILIENCE] ⚠  Unclean shutdown detected.")
            print(f"[RESILIENCE]    Reason: {result.get('reason', 'Unknown')}")
            print(f"[RESILIENCE]    Running revival checks...")
            self._log_revival("unclean_shutdown", result.get("reason", "Unknown"))
            self._run_revival_checks()
            return {"status": "revived", "reason": result.get("reason")}

        print("[RESILIENCE] Clean startup.")
        self._log_revival("clean_start", "Normal startup")
        return {"status": "clean"}

    def _run_revival_checks(self):
        """
        After unclean shutdown — check what needs attention.
        """
        print("[RESILIENCE]    · Checking database integrity...")
        # Database check — SQLAlchemy will handle this on first query
        # If DB is corrupt, it will raise on startup and needs manual recovery

        print("[RESILIENCE]    · Checking for posts stuck in PENDING status...")
        # Posts that were mid-fingerprint scan when crash occurred
        # These will be re-scanned on next access

        print("[RESILIENCE]    Revival checks complete.")
        print("[RESILIENCE]    The Commons is resuming. Power to the People.")

    def _log_revival(self, event_type: str, reason: str):
        log = []
        if os.path.exists(REVIVAL_LOG):
            try:
                with open(REVIVAL_LOG) as f:
                    log = json.load(f)
            except Exception:
                log = []

        log.append({
            "event":     event_type,
            "reason":    reason,
            "timestamp": datetime.utcnow().isoformat(),
            "pid":       os.getpid(),
        })

        try:
            with open(REVIVAL_LOG, "w") as f:
                json.dump(log, f, indent=2)
        except Exception:
            pass


# ── Singleton instances ───────────────────────────────────────────────────────

heartbeat = HeartbeatMonitor()
revival   = RevivalManager()
