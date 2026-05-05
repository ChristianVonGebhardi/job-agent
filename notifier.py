import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(new_jobs, skipped=[]):
    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("BREVO_API_KEY")
    recipient = os.getenv("GMAIL_RECIPIENT")

    if not all([password, sender, recipient]):
        print(">>> Missing email credentials — skipping email")
        return

    # Group new jobs by company
    by_company = {}
    for job in new_jobs:
        company = job["company"]
        if company not in by_company:
            by_company[company] = []
        by_company[company].append(job)

    # Build HTML
    html = "<h2>💼 Daily Job Report</h2>"

    # Skipped section first, so it's more visible even with long lists of new jobs
    if skipped:
        html += "<hr><h3>⚠️ Requires Manual Check</h3>"
        html += "<p style='color:#888;font-size:12px;'>These companies could not be processed automatically:</p>"
        html += "<ul>"
        for s in skipped:
            url_part = f' — <a href="{s["url"]}">{s["url"]}</a>' if s["url"] else ""
            html += f'<li><strong>{s["company"]}</strong> ({s["reason"]}){url_part}</li>'
        html += "</ul>"

    if new_jobs:
        html += f"<p><strong>{len(new_jobs)} new job(s)</strong> found across {len(by_company)} company/companies.</p>"
        for company, jobs in by_company.items():
            html += f"<h3>{company} ({len(jobs)} new)</h3><ul>"
            for job in jobs:
                location = f" — {job['location']}" if job.get('location') else ""
                html += f'<li><a href="{job["url"]}">{job["title"]}</a>{location}</li>'
            html += "</ul>"
    else:
        html += "<p>No new job postings since yesterday.</p>"

    html += f"<hr><p style='color:#aaa;font-size:11px;'>Job Agent — {__import__('time').strftime('%Y-%m-%d %H:%M UTC')}</p>"

    subject = f"💼 Job Report — {len(new_jobs)} new" if new_jobs else "💼 Job Report — No new postings"

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": password,
            "Content-Type": "application/json"
        },
        json={
            "sender": {"email": sender},
            "to": [{"email": recipient}],
            "subject": subject,
            "htmlContent": html
        }
    )

    if response.status_code == 201:
        print(f">>> Email sent: {len(new_jobs)} new jobs, {len(skipped)} skipped")
    else:
        print(f">>> Email failed: {response.status_code} {response.text}")