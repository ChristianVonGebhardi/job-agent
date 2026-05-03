import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_email(new_jobs):
    if not new_jobs:
        print(">>> No new jobs — skipping email")
        return

    sender = os.getenv("GMAIL_SENDER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    recipient = os.getenv("GMAIL_RECIPIENT")

    if not all([sender, password, recipient]):
        print(">>> Missing email credentials — skipping email")
        return

    # Group jobs by company
    by_company = {}
    for job in new_jobs:
        company = job["company"]
        if company not in by_company:
            by_company[company] = []
        by_company[company].append(job)

    # Build HTML email
    html = """
    <html><body>
    <h2 style="color:#2c3e50;">⚡ New Job Postings</h2>
    <p style="color:#666;">The following new positions were found today:</p>
    """

    for company, jobs in by_company.items():
        html += f"""
        <h3 style="color:#2980b9;border-bottom:1px solid #eee;padding-bottom:4px;">
            {company} ({len(jobs)} new)
        </h3>
        <ul>
        """
        for job in jobs:
            location = f" — {job['location']}" if job.get('location') else ""
            html += f"""
            <li style="margin-bottom:8px;">
                <a href="{job['url']}" style="color:#2c3e50;font-weight:bold;">
                    {job['title']}
                </a>
                <span style="color:#888;">{location}</span>
            </li>
            """
        html += "</ul>"

    html += f"""
    <hr>
    <p style="color:#aaa;font-size:12px;">
        {len(new_jobs)} new job(s) found across {len(by_company)} company/companies.
    </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"⚡ {len(new_jobs)} New Job Posting(s) Found"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        print(f">>> Email sent: {len(new_jobs)} new jobs")
    except Exception as e:
        print(f">>> Email failed: {e}")