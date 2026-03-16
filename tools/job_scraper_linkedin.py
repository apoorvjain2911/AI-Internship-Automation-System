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


def scrape_linkedin_jobs(keyword: str, limit: int = 20):
    url = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keyword + ' internship')}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
    except Exception:
        return []

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.select(".base-search-card")

    jobs = []
    for card in cards[:limit]:
        title_node = card.select_one("h3.base-search-card__title") or card.find("h3")
        company_node = card.select_one("h4.base-search-card__subtitle") or card.find("h4")
        location_node = card.select_one(".job-search-card__location")
        link_node = card.select_one("a.base-card__full-link") or card.find("a")
        posted_node = card.select_one("time")

        if not title_node or not company_node or not link_node:
            continue

        title = title_node.get_text(" ", strip=True)
        company = company_node.get_text(" ", strip=True)
        location_text = location_node.get_text(" ", strip=True) if location_node else ""
        posted_raw = posted_node.get_text(" ", strip=True) if posted_node else ""
        job_link = link_node.get("href", "")

        short_text = " ".join([title, company, location_text])

        jobs.append({
            "source": "linkedin",
            "source_job_id": job_link,
            "title": title,
            "company": company,
            "skills_required": extract_skills_from_text(short_text),
            "work_mode": infer_work_mode(short_text),
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
