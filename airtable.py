import requests
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_companies():
    """Fetch company list from Airtable."""
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")

    if not all([token, base_id, table_id]):
        raise ValueError("Missing Airtable credentials in .env")

    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {"Authorization": f"Bearer {token}"}
    companies = []
    offset = None

    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for record in data.get("records", []):
            fields = record.get("fields", {})
            company = (fields.get("Company") or "").strip()
            careers_url = (fields.get("Careers URL") or "").strip()

            # Skip empty rows
            if not company and not careers_url:
                continue

            companies.append({
                "company": company,
                "url": careers_url
            })

        offset = data.get("offset")
        if not offset:
            break

    print(f">>> Loaded {len(companies)} companies from Airtable")
    return companies