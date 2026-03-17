from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from tools.job_scraper import (
    extract_skills_from_text,
    infer_work_mode,
    parse_posted_days_ago,
    request_with_retries,
)


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


BASE_URL = "https://wellfound.com"


def _make_absolute(url: str):
    if not url:
        return ""
    if url.startswith("http"):
        return url
    return f"{BASE_URL}{url}"


def scrape_wellfound_jobs(keyword: str, limit: int = 20):
    url = f"{BASE_URL}/jobs?query={quote_plus(keyword + ' internship')}"

    try:
        response = request_with_retries(url, headers=HEADERS)
    except Exception:
        return []

    if not response or response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select("a[href*='/jobs/']")

    jobs = []
    seen_links = set()

    for link_node in cards:
        if len(jobs) >= limit:
            break

        href = _make_absolute(link_node.get("href", ""))
        if not href or href in seen_links:
            continue

        seen_links.add(href)
        text = link_node.get_text(" ", strip=True)

        if not text or len(text) < 5:
            continue

        parts = [part.strip() for part in text.split("\n") if part.strip()]
        title = parts[0] if parts else text[:80]
        company = parts[1] if len(parts) > 1 else "Unknown"

        text_blob = " ".join([title, company, text])

        jobs.append({
            "source": "wellfound",
            "source_job_id": href,
            "title": title,
            "company": company,
            "skills_required": extract_skills_from_text(text_blob),
            "work_mode": infer_work_mode(text_blob),
            "location_text": "",
            "stipend_raw": "",
            "stipend_min": None,
            "duration_raw": "",
            "duration_months": None,
            "posted_raw": "",
            "posted_days_ago": parse_posted_days_ago(""),
            "linkedin_url": f"https://www.linkedin.com/search/results/companies/?keywords={company}",
            "job_link": href,
        })

    return jobs
