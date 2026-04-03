#!/usr/bin/env python3
"""
watchdog.py — The Commons Watchdog

Keeps The Commons running.
If it crashes — restarts it automatically.
If it won't start — waits and tries again.

Run this instead of main.py when you want auto-restart:

    python watchdog.py

For Termux background running:
    nohup python watchdog.py &

For Railway cloud deployment:
    Railway handles auto-restart automatically.
    You don't need this script on Railway.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

import subprocess
import sys
import time
import os
from datetime import datetime

RESTART_DELAY    = 5    # seconds to wait before restarting after crash
MAX_RESTARTS     = 10   # max restarts within RESTART_WINDOW
RESTART_WINDOW   = 300  # seconds (5 minutes)
BACKOFF_SECONDS  = 60   # wait longer if restarting too fast

restart_times = []


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[WATCHDOG] {ts} — {msg}", flush=True)


def too_many_restarts() -> bool:
    """Check if we're restarting too frequently."""
    now = time.time()
    recent = [t for t in restart_times if now - t < RESTART_WINDOW]
    restart_times.clear()
    restart_times.extend(recent)
    return len(recent) >= MAX_RESTARTS


def run():
    log("The Commons Watchdog started.")
    log("Power to the People.")
    log("Press Ctrl+C to stop.")
    print()

    python = sys.executable
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")

    while True:
        try:
            log(f"Starting The Commons...")
            process = subprocess.Popen(
                [python, script],
                cwd=os.path.dirname(script)
            )
            process.wait()
            exit_code = process.returncode

            if exit_code == 0:
                log("The Commons exited cleanly. Watchdog stopping.")
                break

            # Crash detected
            log(f"The Commons stopped (exit code {exit_code}).")
            restart_times.append(time.time())

            if too_many_restarts():
                log(f"Too many restarts in {RESTART_WINDOW}s. "
                    f"Waiting {BACKOFF_SECONDS}s before trying again...")
                time.sleep(BACKOFF_SECONDS)
                restart_times.clear()
            else:
                log(f"Restarting in {RESTART_DELAY}s...")
                time.sleep(RESTART_DELAY)

        except KeyboardInterrupt:
            log("Watchdog stopped by user.")
            try:
                process.terminate()
            except Exception:
                pass
            break

        except Exception as e:
            log(f"Watchdog error: {e}")
            time.sleep(RESTART_DELAY)


if __name__ == "__main__":
    run()
