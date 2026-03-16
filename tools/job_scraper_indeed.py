import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from tools.job_scraper import (
    extract_skills_from_text,
    infer_work_mode,
    parse_posted_days_ago,
)


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


BASE_URL = "https://in.indeed.com"


def _make_absolute(url: str):
    if not url:
        return ""
    if url.startswith("http"):
        return url
    return f"{BASE_URL}{url}"


def scrape_indeed_jobs(keyword: str, limit: int = 20):
    url = f"{BASE_URL}/jobs?q={quote_plus(keyword + ' internship')}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
    except Exception:
        return []

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select(".job_seen_beacon, .result")

    jobs = []
    for card in cards[:limit]:
        title_node = card.select_one("h2.jobTitle") or card.find("h2")
        company_node = card.select_one("[data-testid='company-name']") or card.select_one(".companyName")
        location_node = card.select_one("[data-testid='text-location']") or card.select_one(".companyLocation")
        posted_node = card.select_one(".date")
        link_node = card.select_one("h2 a") or card.find("a")

        if not title_node or not company_node or not link_node:
            continue

        title = title_node.get_text(" ", strip=True)
        company = company_node.get_text(" ", strip=True)
        location_text = location_node.get_text(" ", strip=True) if location_node else ""
        posted_raw = posted_node.get_text(" ", strip=True) if posted_node else ""
        job_link = _make_absolute(link_node.get("href", ""))

        text_blob = " ".join([title, company, location_text])

        jobs.append({
            "source": "indeed",
            "source_job_id": job_link,
            "title": title,
            "company": company,
            "skills_required": extract_skills_from_text(text_blob),
            "work_mode": infer_work_mode(text_blob),
            "location_text": location_text,
            "stipend_raw": "",
            "stipend_min": None,
            "duration_raw": "",
            "duration_months": None,
            "posted_raw": posted_raw,
            "posted_days_ago": parse_posted_days_ago(posted_raw),
            "linkedin_url": f"https://www.linkedin.com/search/results/companies/?keywords={company}",
            "job_link": job_link,
        })

    return jobs
