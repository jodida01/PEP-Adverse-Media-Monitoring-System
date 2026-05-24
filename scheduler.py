import schedule
import time
import subprocess
import sys

def job():
    print("Running AML scan...")

    # Use SAME Python interpreter as current venv
    subprocess.run([sys.executable, "app.py"])

# Run every 24 hours
schedule.every(24).hours.do(job)

# Run immediately when started
job()

while True:
    schedule.run_pending()
    time.sleep(60)