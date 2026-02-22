# scheduler.py — Runs the fetcher daily at a set time

import schedule
import time
from fetcher import fetch_all

RUN_AT = "08:00"


def job():
    print(f"\n{'=' * 60}")
    print(f"  Daily fare fetch")
    print(f"{'=' * 60}")
    try:
        fetch_all()
    except Exception as e:
        print(f"[CRITICAL] Unhandled error: {e}")


if __name__ == "__main__":
    print(f"Scheduler started. Will run daily at {RUN_AT}.")
    print("Running an immediate fetch now...\n")
    job()
    schedule.every().day.at(RUN_AT).do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)
