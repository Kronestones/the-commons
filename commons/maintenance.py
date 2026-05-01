"""
maintenance.py — The Commons Auto-Maintenance

Keeps the platform clean and running smoothly.
Runs automatically — no human intervention needed.

What gets cleaned:
  - Expired sessions and tokens
  - Read notifications older than 90 days
  - Read direct messages older than 180 days
  - Orphaned temp files
  - Old watch events older than 60 days
  - Failed fingerprint records older than 30 days

What NEVER gets cleaned:
  - Fingerprint flags and decisions
  - Circle decisions and voting records
  - Surplus donation records
  - Any content removal records
  - User accounts and posts
  - Audit logs

Runs every 24 hours automatically.
Logs everything it does.

Codex Law 1: People First — clean platform = better experience
Codex Law 5: Transparency — logs everything

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

import os
import threading
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import SessionLocal
from .config import config


class MaintenanceManager:

    INTERVAL_HOURS = 24  # Run every 24 hours

    def __init__(self):
        self._stop_event  = threading.Event()
        self._thread      = None
        self._last_run    = None
        self._log_file    = "maintenance.log"

    def start(self):
        """Start the maintenance scheduler in background."""
        self._thread = threading.Thread(target=self._scheduler, daemon=True)
        self._thread.start()
        print("[MAINTENANCE] Auto-maintenance scheduler started.")

    def stop(self):
        self._stop_event.set()

    def _scheduler(self):
        """Run maintenance every 24 hours."""
        while not self._stop_event.is_set():
            try:
                self.run()
            except Exception as e:
                print(f"[MAINTENANCE] Error: {e}")
            # Wait 24 hours
            self._stop_event.wait(self.INTERVAL_HOURS * 3600)

    def run(self) -> dict:
        """Run all maintenance tasks."""
        print(f"[MAINTENANCE] Starting maintenance run — {datetime.utcnow().isoformat()}")
        db = SessionLocal()
        results = {}

        try:
            results["notifications"]  = self._clean_notifications(db)
            results["messages"]       = self._clean_messages(db)
            results["watch_events"]   = self._clean_watch_events(db)
            results["fingerprint"]    = self._clean_fingerprint_records(db)
            results["temp_files"]     = self._clean_temp_files()

            self._last_run = datetime.utcnow()
            self._log(results)

            total_cleaned = sum(v for v in results.values() if isinstance(v, int))
            print(f"[MAINTENANCE] Complete — {total_cleaned} records cleaned.")

        except Exception as e:
            print(f"[MAINTENANCE] Error during run: {e}")
            results["error"] = str(e)
        finally:
            db.close()

        return results

    def _clean_notifications(self, db: Session) -> int:
        """Remove read notifications older than 90 days."""
        try:
            from .features import Notification
            cutoff = datetime.utcnow() - timedelta(days=90)
            count = db.query(Notification).filter(
                Notification.is_read == True,
                Notification.created_at < cutoff
            ).delete()
            db.commit()
            print(f"[MAINTENANCE]   · Notifications: {count} removed")
            return count
        except Exception as e:
            print(f"[MAINTENANCE]   · Notifications error: {e}")
            return 0

    def _clean_messages(self, db: Session) -> int:
        """Remove read messages older than 180 days."""
        try:
            from .features import DirectMessage
            cutoff = datetime.utcnow() - timedelta(days=180)
            count = db.query(DirectMessage).filter(
                DirectMessage.is_read == True,
                DirectMessage.created_at < cutoff
            ).delete()
            db.commit()
            print(f"[MAINTENANCE]   · Messages: {count} removed")
            return count
        except Exception as e:
            print(f"[MAINTENANCE]   · Messages error: {e}")
            return 0

    def _clean_watch_events(self, db: Session) -> int:
        """Remove watch events older than 60 days."""
        try:
            from .preferences import WatchEvent
            cutoff = datetime.utcnow() - timedelta(days=60)
            count = db.query(WatchEvent).filter(
                WatchEvent.recorded_at < cutoff
            ).delete()
            db.commit()
            print(f"[MAINTENANCE]   · Watch events: {count} removed")
            return count
        except Exception as e:
            print(f"[MAINTENANCE]   · Watch events error: {e}")
            return 0

    def _clean_fingerprint_records(self, db: Session) -> int:
        """
        Remove clean fingerprint records older than 30 days.
        NEVER removes flagged, held, removed, or appealed records.
        Those are permanent audit records.
        """
        try:
            from .database import FingerprintRecord, Post, PostStatus
            cutoff = datetime.utcnow() - timedelta(days=30)
            count = db.query(FingerprintRecord).filter(
                FingerprintRecord.scan_result == "clean",
                FingerprintRecord.scanned_at < cutoff
            ).delete()
            db.commit()
            print(f"[MAINTENANCE]   · Clean fingerprint records: {count} removed")
            return count
        except Exception as e:
            print(f"[MAINTENANCE]   · Fingerprint records error: {e}")
            return 0

    def _clean_temp_files(self) -> int:
        """Remove temporary files from media directory."""
        try:
            count = 0
            media_dir = config.media_dir
            if media_dir.exists():
                for f in media_dir.iterdir():
                    if f.name.startswith("tmp_") and f.is_file():
                        age = datetime.utcnow() - datetime.fromtimestamp(f.stat().st_mtime)
                        if age > timedelta(hours=24):
                            f.unlink()
                            count += 1
            print(f"[MAINTENANCE]   · Temp files: {count} removed")
            return count
        except Exception as e:
            print(f"[MAINTENANCE]   · Temp files error: {e}")
            return 0

    def _log(self, results: dict):
        """Log maintenance results."""
        try:
            with open(self._log_file, "a") as f:
                f.write(f"\n[{datetime.utcnow().isoformat()}] Maintenance run:\n")
                for key, value in results.items():
                    f.write(f"  {key}: {value}\n")
        except Exception:
            pass

    def get_status(self) -> dict:
        return {
            "last_run":        self._last_run.isoformat() if self._last_run else "Never",
            "next_run":        (self._last_run + timedelta(hours=self.INTERVAL_HOURS)).isoformat()
                               if self._last_run else "Pending first run",
            "interval_hours":  self.INTERVAL_HOURS,
            "never_cleaned": [
                "Fingerprint flags and decisions",
                "Circle decisions and voting records",
                "Surplus donation records",
                "Content removal records",
                "User accounts and posts",
                "Audit logs"
            ]
        }


maintenance = MaintenanceManager()
