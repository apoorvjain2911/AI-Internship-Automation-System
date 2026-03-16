from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import io
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

# Import tools
from tools.job_scraper import scrape_internshala
from tools.job_scraper_linkedin import scrape_linkedin_jobs
from tools.job_scraper_naukri import scrape_naukri_jobs
from tools.job_scraper_indeed import scrape_indeed_jobs
from tools.job_scraper_wellfound import scrape_wellfound_jobs
from tools.job_scraper_unstop import scrape_unstop_jobs
from tools.ranker import rank_jobs

app = FastAPI(title="AI Internship Auto Apply System")

# ----------------------------
# CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# In-memory storage
# ----------------------------
last_resume_data = {}

# ----------------------------
# Health Check
# ----------------------------
@app.get("/")
def home():
    return {"message": "Server is running 🚀"}

# ----------------------------
# Resume Parsing Logic
# ----------------------------
def extract_structured_data(text: str):

    lines = text.splitlines()

    name = ""
    education = ""
    skills = []

    # Extract name
    for line in lines:
        if line.strip():
            name = line.strip()
            break

    # Education
    for line in lines:
        lower = line.lower()
        if "mba" in lower or "bba" in lower or "b.tech" in lower or "btech" in lower:
            education = line.strip()
            break

    skill_keywords = [
        "finance",
        "financial",
        "analysis",
        "accounting",
        "excel",
        "communication",
        "python",
        "data",
        "marketing"
    ]

    for line in lines:
        lower = line.lower()
        for skill in skill_keywords:
            if skill in lower and skill not in skills:
                skills.append(skill)

    return {
        "name": name,
        "education": education,
        "skills": skills
    }


def normalize_work_mode(value: str):
    normalized = (value or "").strip().lower()
    if normalized in {"remote", "hybrid", "on-site", "onsite"}:
        return "on-site" if normalized == "onsite" else normalized
    return ""


def get_sort_value(job, sort_by: str):
    if sort_by == "match_score":
        return job.get("match_score")
    if sort_by == "stipend":
        return job.get("stipend_min")
    if sort_by == "duration":
        return job.get("duration_months")
    if sort_by == "posted_days":
        return job.get("posted_days_ago")
    if sort_by == "company":
        return (job.get("company") or "").lower()
    if sort_by == "title":
        return (job.get("title") or "").lower()
    return job.get("match_score")


def sort_jobs(jobs, sort_by: str, sort_order: str):
    available = []
    missing = []

    for job in jobs:
        value = get_sort_value(job, sort_by)
        if value is None or value == "":
            missing.append(job)
        else:
            available.append(job)

    reverse = sort_order == "desc"
    available.sort(key=lambda item: get_sort_value(item, sort_by), reverse=reverse)
    return available + missing


def normalize_job_url(url: str):
    if not url:
        return ""
    try:
        split = urlsplit(url.strip())
        cleaned_path = split.path.rstrip("/")
        return urlunsplit((split.scheme, split.netloc, cleaned_path, "", ""))
    except Exception:
        return url.strip()


def dedupe_jobs(jobs):
    deduped = []
    seen = set()

    for job in jobs:
        normalized_link = normalize_job_url(job.get("job_link", ""))
        title = (job.get("title") or "").strip().lower()
        company = (job.get("company") or "").strip().lower()
        location = (job.get("location_text") or "").strip().lower()

        key = normalized_link or f"{title}|{company}|{location}"
        if not key or key in seen:
            continue

        seen.add(key)
        deduped.append(job)

    return deduped

# ----------------------------
# Upload Resume
# ----------------------------
@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):

    global last_resume_data

    contents = await file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))

    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    structured = extract_structured_data(text)
    last_resume_data = structured

    return {
        "structured_data": structured
    }

# ----------------------------
# AUTO APPLY PIPELINE
# ----------------------------
@app.post("/auto-apply/")
async def auto_apply(
    keyword: str = "finance",
    sources: str = "all",
    work_mode: Optional[str] = None,
    location_contains: Optional[str] = None,
    min_stipend: Optional[int] = None,
    max_duration_months: Optional[float] = None,
    max_posted_days: Optional[int] = None,
    sort_by: str = "match_score",
    sort_order: str = "desc",
    top_n: int = 50
):

    if not last_resume_data:
        return {"error": "Upload resume first"}

    resume_skills = last_resume_data.get("skills", [])

    if top_n <= 0:
        return {"error": "top_n must be >= 1"}

    scraper_map = {
        "internshala": scrape_internshala,
        "linkedin": scrape_linkedin_jobs,
        "naukri": scrape_naukri_jobs,
        "indeed": scrape_indeed_jobs,
        "wellfound": scrape_wellfound_jobs,
        "unstop": scrape_unstop_jobs,
    }

    requested_sources = [part.strip().lower() for part in (sources or "").split(",") if part.strip()]
    if not requested_sources or "all" in requested_sources:
        selected_sources = list(scraper_map.keys())
    else:
        invalid_sources = [source for source in requested_sources if source not in scraper_map]
        if invalid_sources:
            return {
                "error": (
                    "Invalid source(s): "
                    f"{invalid_sources}. Allowed: {sorted(scraper_map.keys())} or 'all'"
                )
            }
        selected_sources = requested_sources

    source_stats = {
        source: {
            "fetched": 0,
            "after_dedupe": 0,
            "after_filters": 0,
        }
        for source in selected_sources
    }
    source_failures = []

    # 1️⃣ Scrape jobs from selected sources
    merged_jobs = []
    for source in selected_sources:
        scraper = scraper_map[source]
        try:
            source_jobs = scraper(keyword)
            source_stats[source]["fetched"] = len(source_jobs)
            merged_jobs.extend(source_jobs)
        except Exception as exc:
            source_failures.append({"source": source, "reason": str(exc)})

    if not merged_jobs:
        return {
            "error": "No jobs found from selected sources",
            "source_stats": source_stats,
            "source_failures": source_failures,
        }

    jobs = dedupe_jobs(merged_jobs)

    for source in selected_sources:
        source_stats[source]["after_dedupe"] = len([
            job for job in jobs if (job.get("source") or "unknown") == source
        ])

    if min_stipend is not None and min_stipend < 0:
        return {"error": "min_stipend must be >= 0"}
    if max_duration_months is not None and max_duration_months < 0:
        return {"error": "max_duration_months must be >= 0"}
    if max_posted_days is not None and max_posted_days < 0:
        return {"error": "max_posted_days must be >= 0"}

    allowed_sort_by = {"match_score", "stipend", "duration", "posted_days", "company", "title"}
    if sort_by not in allowed_sort_by:
        return {"error": f"Invalid sort_by. Allowed: {sorted(allowed_sort_by)}"}
    if sort_order not in {"asc", "desc"}:
        return {"error": "sort_order must be 'asc' or 'desc'"}

    normalized_mode = normalize_work_mode(work_mode or "")
    normalized_location = (location_contains or "").strip().lower()

    filtered_jobs = []
    for job in jobs:
        job_mode = normalize_work_mode(job.get("work_mode", ""))
        job_location = (job.get("location_text") or "").lower()
        stipend_min = job.get("stipend_min")
        duration_months = job.get("duration_months")
        posted_days_ago = job.get("posted_days_ago")

        if normalized_mode and job_mode != normalized_mode:
            continue
        if normalized_location and normalized_location not in job_location:
            continue
        if min_stipend is not None:
            if stipend_min is None or stipend_min < min_stipend:
                continue
        if max_duration_months is not None:
            if duration_months is None or duration_months > max_duration_months:
                continue
        if max_posted_days is not None:
            if posted_days_ago is None or posted_days_ago > max_posted_days:
                continue

        filtered_jobs.append(job)

    for source in selected_sources:
        source_stats[source]["after_filters"] = len([
            job for job in filtered_jobs if (job.get("source") or "unknown") == source
        ])

    if not filtered_jobs:
        return {
            "total_jobs_found": len(merged_jobs),
            "total_jobs_after_dedupe": len(jobs),
            "total_jobs_after_filters": 0,
            "source_stats": source_stats,
            "source_failures": source_failures,
            "top_matches": [],
            "message": "No jobs matched selected filters"
        }

    # 2️⃣ Rank jobs
    ranked_jobs = rank_jobs(resume_skills, filtered_jobs)

    # 3️⃣ Sort jobs
    ranked_jobs = sort_jobs(ranked_jobs, sort_by=sort_by, sort_order=sort_order)

    # 4️⃣ Take top N after filters and sorting
    top_jobs = ranked_jobs[:top_n]

    # 5️⃣ Prepare results with skill-gap details for each job
    results = []

    for job in top_jobs:
        required_skills = job.get("skills_required", [])
        matched_skills = job.get("matched_skills", [])
        missing_skills = [
            skill for skill in required_skills
            if skill not in matched_skills
        ]

        results.append({
            "source": job.get("source", "unknown"),
            "company": job["company"],
            "title": job["title"],
            "match_score": job["match_score"],
            "linkedin_search": job["linkedin_url"],
            "job_link": job["job_link"],
            "job_meta": {
                "work_mode": job.get("work_mode", "unknown"),
                "location_text": job.get("location_text", ""),
                "stipend_raw": job.get("stipend_raw", ""),
                "stipend_min": job.get("stipend_min"),
                "duration_raw": job.get("duration_raw", ""),
                "duration_months": job.get("duration_months"),
                "posted_raw": job.get("posted_raw", ""),
                "posted_days_ago": job.get("posted_days_ago")
            },
            "skills_detail": {
                "required_skills": required_skills,
                "matched_skills": matched_skills,
                "missing_from_resume": missing_skills
            }
        })

    return {
        "total_jobs_found": len(merged_jobs),
        "total_jobs_after_dedupe": len(jobs),
        "total_jobs_after_filters": len(filtered_jobs),
        "source_stats": source_stats,
        "source_failures": source_failures,
        "filters_applied": {
            "sources": selected_sources,
            "work_mode": normalized_mode or None,
            "location_contains": normalized_location or None,
            "min_stipend": min_stipend,
            "max_duration_months": max_duration_months,
            "max_posted_days": max_posted_days,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "top_n": top_n,
        },
        "top_matches": results
    }