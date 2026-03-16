import requests
from bs4 import BeautifulSoup
import time
import re


# Global skill keywords (you can expand this)
SKILL_KEYWORDS = [
    "finance",
    "financial",
    "analysis",
    "accounting",
    "excel",
    "communication",
    "python",
    "data",
    "marketing",
    "auditing",
    "tax",
    "investment",
    "research",
    "forecasting",
    "reporting",
    "budgeting"
]


def extract_skills_from_text(text):
    found_skills = []

    lower_text = text.lower()

    for skill in SKILL_KEYWORDS:
        if skill in lower_text:
            found_skills.append(skill)

    return list(set(found_skills))


def parse_stipend_min(stipend_text: str):
    if not stipend_text:
        return None

    normalized = stipend_text.lower().replace(",", "")
    numbers = [int(value) for value in re.findall(r"\d+", normalized)]

    if not numbers:
        return None

    # "5k" style support
    if "k" in normalized:
        return min(numbers) * 1000

    return min(numbers)


def parse_duration_months(duration_text: str):
    if not duration_text:
        return None

    match = re.search(r"(\d+)\s*(month|months|week|weeks)", duration_text.lower())
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if "week" in unit:
        return round(value / 4, 2)

    return value


def parse_posted_days_ago(posted_text: str):
    if not posted_text:
        return None

    text = posted_text.lower().strip()

    if "today" in text or "just now" in text:
        return 0

    match = re.search(r"(\d+)\s*(day|days|week|weeks|month|months)", text)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if "week" in unit:
        return value * 7
    if "month" in unit:
        return value * 30

    return value


def infer_work_mode(text: str):
    if not text:
        return "unknown"

    lower = text.lower()

    if "hybrid" in lower:
        return "hybrid"
    if "work from home" in lower or "remote" in lower:
        return "remote"
    if "in office" in lower or "on-site" in lower or "onsite" in lower:
        return "on-site"

    return "unknown"


def extract_location_text(job_soup):
    location_parts = []

    location_nodes = job_soup.select(
        ".location_link, .location_names, .locations, [id*='location']"
    )

    for node in location_nodes:
        node_text = node.get_text(" ", strip=True)
        if node_text and node_text.lower() not in {"location", "locations"}:
            location_parts.append(node_text)

    unique_parts = []
    for part in location_parts:
        if part not in unique_parts:
            unique_parts.append(part)

    return ", ".join(unique_parts[:3])


def extract_first_matching_text(job_soup, selectors):
    for selector in selectors:
        node = job_soup.select_one(selector)
        if node:
            value = node.get_text(" ", strip=True)
            if value:
                return value
    return ""


def scrape_internshala(keyword: str):
    url = f"https://internshala.com/internships/{keyword}-internship/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    jobs = []

    cards = soup.find_all("div", class_="internship_meta")

    for card in cards[:10]:  # Limit to 10 jobs

        title_tag = card.find("a")
        company_tag = card.find("div", class_="company_name")

        if not title_tag or not company_tag:
            continue

        title = title_tag.text.strip()
        company = company_tag.text.strip().replace("\n", "").replace("Actively hiring", "").strip()

        job_link = "https://internshala.com" + title_tag["href"]

        # ---------------------------
        # Visit job page for skill and metadata extraction
        # ---------------------------
        try:
            job_response = requests.get(job_link, headers=headers)
            job_soup = BeautifulSoup(job_response.text, "html.parser")

            description_div = job_soup.find("div", class_="internship_details")
            description_text = description_div.get_text(separator=" ") if description_div else ""

            skills_required = extract_skills_from_text(description_text)

            stipend_raw = extract_first_matching_text(
                job_soup,
                [
                    ".stipend",
                    ".salary",
                    ".item_body",
                    "[class*='stipend']"
                ]
            )

            duration_raw = extract_first_matching_text(
                job_soup,
                [
                    ".other_detail_item .item_body",
                    "[class*='duration']",
                    ".duration"
                ]
            )

            posted_raw = extract_first_matching_text(
                job_soup,
                [
                    ".status-success",
                    ".posted_on",
                    "[class*='posted']",
                    "[class*='status']"
                ]
            )

            work_mode = infer_work_mode(description_text)
            location_text = extract_location_text(job_soup)
            stipend_min = parse_stipend_min(stipend_raw)
            duration_months = parse_duration_months(duration_raw)
            posted_days_ago = parse_posted_days_ago(posted_raw)

            time.sleep(1)  # polite delay

        except Exception:
            skills_required = []
            work_mode = "unknown"
            location_text = ""
            stipend_raw = ""
            stipend_min = None
            duration_raw = ""
            duration_months = None
            posted_raw = ""
            posted_days_ago = None

        jobs.append({
            "source": "internshala",
            "source_job_id": title_tag.get("href", ""),
            "title": title,
            "company": company,
            "skills_required": skills_required,
            "work_mode": work_mode,
            "location_text": location_text,
            "stipend_raw": stipend_raw,
            "stipend_min": stipend_min,
            "duration_raw": duration_raw,
            "duration_months": duration_months,
            "posted_raw": posted_raw,
            "posted_days_ago": posted_days_ago,
            "linkedin_url": f"https://www.linkedin.com/search/results/companies/?keywords={company}",
            "job_link": job_link
        })

    return jobs