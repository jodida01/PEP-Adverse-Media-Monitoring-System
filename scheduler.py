import os
import schedule
import time
from datetime import datetime

from app import run_scan

SCAN_INTERVAL_HOURS = int(os.environ.get("SCAN_INTERVAL_HOURS", "24"))


def job():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{now}] Running AML scan...")
    run_scan()

if __name__ == "__main__":
    schedule.every(SCAN_INTERVAL_HOURS).hours.do(job)

    # Run once immediately on startup.
    job()

    while True:
        schedule.run_pending()
        time.sleep(60)