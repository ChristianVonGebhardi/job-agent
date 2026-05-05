import json
import os
from datetime import datetime

DATA_FILE = "/data/jobs_latest.json"

def load_previous():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_current(data):
    #os.makedirs("data", exist_ok=True) # remove the os.makedirs line since Railway manages the /data directory
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def find_new_jobs(previous, current):
    """Compare current vs previous, return only new jobs."""
    new_jobs = []

    for key, entry in current.items():
        prev_entry = previous.get(key, {})
        prev_ids = {job["id"] for job in prev_entry.get("jobs", [])}

        for job in entry["jobs"]:
            if job["id"] not in prev_ids:
                new_jobs.append({
                    "company": entry["company"],
                    "url": entry["url"],
                    **job
                })

    return new_jobs

def run_comparison(current_data):
    """Load previous, compare, save current. Returns new jobs."""
    previous = load_previous()
    new_jobs = find_new_jobs(previous, current_data)
    save_current(current_data)
    print(f"\n>>> Found {len(new_jobs)} new jobs")
    return new_jobs