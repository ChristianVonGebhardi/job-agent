from flask import Flask, render_template, jsonify
from airtable import fetch_companies
from fetcher import fetch_all_companies
from comparator import run_comparison, load_previous
from notifier import send_email
import threading
import schedule
import time
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

cache = {
    "new_jobs": [],
    "all_jobs": {},
    "last_updated": None,
    "status": "idle"
}

def run_pipeline():
    cache["status"] = "running"
    try:
        companies = fetch_companies()
        results, skipped = fetch_all_companies(companies)
        new_jobs = run_comparison(results)
        send_email(new_jobs, skipped)
        cache["new_jobs"] = new_jobs
        cache["all_jobs"] = results
        cache["last_updated"] = time.strftime("%Y-%m-%d %H:%M")
        cache["status"] = "done"
        print(f">>> Pipeline complete: {len(new_jobs)} new jobs")
    except Exception as e:
        cache["status"] = "error"
        cache["last_updated"] = time.strftime("%Y-%m-%d %H:%M")
        print(f">>> Pipeline failed: {e}")

def start_scheduler():
    # 6pm CET = 17:00 UTC (adjust for daylight saving if needed)
    schedule.every().day.at("16:00").do(run_pipeline) # set to 16:00 UTC to run at 18:00 CET during daylight saving time
    print(">>> Scheduler started — runs daily at 17:00 UTC (6pm CET)")
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def status():
    return jsonify({
        "status": cache["status"],
        "last_updated": cache["last_updated"],
        "new_jobs_count": len(cache["new_jobs"])
    })

@app.route("/api/results")
def results():
    return jsonify({
        "new_jobs": cache["new_jobs"],
        "total_companies": len(cache["all_jobs"]),
        "total_jobs": sum(
            len(e["jobs"]) for e in cache["all_jobs"].values()
        )
    })

@app.route("/api/refresh", methods=["POST"])
def refresh():
    if cache["status"] != "running":
        thread = threading.Thread(target=run_pipeline)
        thread.daemon = True
        thread.start()
    return jsonify({"status": "started"})

# test email endpoint to verify notifier functionality without running the full pipeline
@app.route("/api/test-email", methods=["POST"])
def test_email():
    from notifier import send_email
    test_jobs = [{
        "company": "Test Company",
        "title": "Test Engineer",
        "location": "Munich",
        "url": "https://example.com"
    }]
    send_email(test_jobs)
    return jsonify({"status": "attempted"})

#debug endpoint to check the count of companies and jobs in the latest saved data
#Open https://job-agent-production-201d.up.railway.app/api/debug/jobs-count in your browser to confirm the file exists and has data.
@app.route("/api/debug/jobs-count")
def jobs_count():
    from comparator import load_previous
    data = load_previous()
    return jsonify({
        "companies": len(data),
        "total_jobs": sum(len(e["jobs"]) for e in data.values())
    })

if __name__ == "__main__":
    # Load existing results on startup
    previous = load_previous()
    if previous:
        cache["all_jobs"] = previous
        cache["status"] = "done"
        cache["last_updated"] = "previous run"

    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)