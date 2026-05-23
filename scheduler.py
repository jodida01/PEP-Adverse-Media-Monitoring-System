import schedule
import time
import subprocess

def job():
    print("Running AML scan...")
    subprocess.run(["python", "app.py"])

# run every 24 hours
schedule.every(24).hours.do(job)

# optional: run immediately once on startup
job()

while True:
    schedule.run_pending()
    time.sleep(60)