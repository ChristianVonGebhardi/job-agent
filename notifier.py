import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(new_jobs):
    if not new_jobs:
        print(">>> No new jobs — skipping email")
        return

    api_key = os.getenv("BREVO_API_KEY")
    sender = os.getenv("GMAIL_SENDER")
    recipient = os.getenv("GMAIL_RECIPIENT")

    if not all([api_key, sender, recipient]):
        print(">>> Missing email credentials — skipping email")
        return

    # Group jobs by company
    by_company = {}
    for job in new_jobs:
        company = job["company"]
        if company not in by_company:
            by_company[company] = []
        by_company[company].append(job)

    # Build HTML
    html = "<h2>⚡ New Job Postings</h2>"
    for company, jobs in by_company.items():
        html += f"<h3>{company} ({len(jobs)} new)</h3><ul>"
        for job in jobs:
            location = f" — {job['location']}" if job.get('location') else ""
            html += f'<li><a href="{job["url"]}">{job["title"]}</a>{location}</li>'
        html += "</ul>"
    html += f"<p>{len(new_jobs)} new job(s) found.</p>"

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": api_key,
            "Content-Type": "application/json"
        },
        json={
            "sender": {"email": sender},
            "to": [{"email": recipient}],
            "subject": f"⚡ {len(new_jobs)} New Job Posting(s) Found",
            "htmlContent": html
        }
    )

    if response.status_code == 201:
        print(f">>> Email sent: {len(new_jobs)} new jobs")
    else:
        print(f">>> Email failed: {response.status_code} {response.text}")