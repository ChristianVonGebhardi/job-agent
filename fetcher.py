import requests
import os
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

SUPPORTED_ATS = ["greenhouse.io", "smartrecruiters.com", "ashbyhq.com"]
UNSUPPORTED_ATS = ["icims.com", "myworkdayjobs.com", "lever.co"]

def detect_ats(url):
    for ats in SUPPORTED_ATS + UNSUPPORTED_ATS:
        if ats in url:
            return ats
    return "unknown"

def normalize_url(url):
    """Convert web URLs to API URLs where needed."""
    # jobs.ashbyhq.com/Company → api.ashbyhq.com/posting-api/job-board/Company
    if "jobs.ashbyhq.com/" in url:
        slug = url.split("jobs.ashbyhq.com/")[1].split("?")[0].split("/")[0]
        return f"https://api.ashbyhq.com/posting-api/job-board/{slug}"

    # job-boards.eu.greenhouse.io/company → EU Greenhouse API
    if "job-boards.eu.greenhouse.io/" in url:
        slug = url.split("job-boards.eu.greenhouse.io/")[1].split("?")[0]
        return f"https://job-boards.eu.greenhouse.io/api/v1/boards/{slug}/jobs"

    # Already an API URL — use as-is
    return url

def parse_jobs(url, response_json):
    """Extract jobs into a unified format regardless of ATS."""
    jobs = []

    try:
        # Greenhouse
        if "greenhouse.io" in url:
            for job in response_json.get("jobs", []):
                jobs.append({
                    "id": str(job.get("id", "")),
                    "title": job.get("title", ""),
                    "location": job.get("location", {}).get("name", ""),
                    "url": job.get("absolute_url", ""),
                    "updated_at": job.get("updated_at", "")
                })

        # SmartRecruiters
        elif "smartrecruiters.com" in url:
            for job in response_json.get("content", []):
                jobs.append({
                    "id": str(job.get("id", "")),
                    "title": job.get("name", ""),
                    "location": job.get("location", {}).get("city", ""),
                    "url": f"https://jobs.smartrecruiters.com/{job.get('company', {}).get('identifier', '')}/{job.get('id', '')}",
                    "updated_at": job.get("releasedDate", "")
                })

        # Ashby
        elif "ashbyhq.com" in url:
            for job in response_json.get("jobPostings", []):
                jobs.append({
                    "id": str(job.get("id", "")),
                    "title": job.get("title", ""),
                    "location": job.get("locationName", ""),
                    "url": job.get("jobUrl", ""),
                    "updated_at": job.get("publishedDate", "")
                })

    except Exception as e:
        print(f"    Parse error for {url}: {e}")

    return jobs

def fetch_jobs_from_url(company, url):
    """Fetch jobs from a single URL. Returns list of jobs or empty list."""
    url = url.strip()
    if not url:
        print(f"  Skipping {company}: empty URL")
        return []

    ats = detect_ats(url)

    if ats in UNSUPPORTED_ATS or ats == "unknown":
        print(f"  Skipping {company}: unsupported ATS ({ats})")
        return []

    api_url = normalize_url(url)

    try:
        response = requests.get(api_url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
        })
        response.raise_for_status()
        jobs = parse_jobs(api_url, response.json())
        print(f"  ✓ {company}: {len(jobs)} jobs")
        return jobs

    except requests.exceptions.Timeout:
        print(f"  ✗ {company}: timeout")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"  ✗ {company}: HTTP {e.response.status_code}")
        return []
    except Exception as e:
        print(f"  ✗ {company}: {e}")
        return []

def fetch_all_companies(companies):
    """
    companies: list of dicts with 'company' and 'url' keys
    Returns: dict keyed by 'company|url' with job lists and skipped entries
    """
    all_jobs = {}
    skipped = []

    for entry in companies:
        company = (entry.get("company") or "").strip()
        url = (entry.get("url") or "").strip()

        if not company and not url:
            continue
        if not company:
            skipped.append({"company": "Unknown", "url": url, "reason": "missing company name"})
            continue
        if not url:
            skipped.append({"company": company, "url": "", "reason": "missing URL"})
            continue

        ats = detect_ats(url)
        if ats in UNSUPPORTED_ATS or ats == "unknown":
            skipped.append({"company": company, "url": url, "reason": f"unsupported ATS ({ats})"})
            print(f"  Skipping {company}: unsupported ATS ({ats})")
            continue

        key = f"{company}|{url}"
        print(f"\n>>> Fetching: {company}")
        all_jobs[key] = {
            "company": company,
            "url": url,
            "jobs": fetch_jobs_from_url(company, url)
        }

    return all_jobs, skipped