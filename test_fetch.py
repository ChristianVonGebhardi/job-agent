from airtable import fetch_companies
from fetcher import fetch_all_companies
from comparator import run_comparison
from notifier import send_email

companies = fetch_companies()
results, skipped = fetch_all_companies(companies)
new_jobs = run_comparison(results)

print(f"\n=== SKIPPED ===")
for s in skipped:
    print(f"{s['company']}: {s['reason']} ({s['url']})")

print(f"\n=== NEW JOBS ===")
for job in new_jobs:
    print(f"{job['company']}: {job['title']} ({job['location']})")
    print(f"  {job['url']}")

# Test with one fake job
#test_jobs = [{
#    "company": "Test Company",
#    "title": "Test Job",
#    "location": "Munich",
#    "url": "https://example.com"
#}]
#send_email(test_jobs)