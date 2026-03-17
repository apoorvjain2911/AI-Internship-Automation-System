# AI Internship Automation System

An internship discovery and matching platform with a FastAPI backend and React frontend.

Upload your resume, fetch internships from multiple platforms, rank by resume-job fit, and review missing skills for each job.

## Features

- Resume upload and parsing (PDF)
- Multi-platform internship aggregation
	- Internshala
	- LinkedIn
	- Naukri
	- Indeed
	- Wellfound
	- Unstop
- Job deduplication across platforms
- Skill match scoring and skill-gap analysis
- Advanced filters
	- work mode
	- location contains
	- minimum stipend
	- maximum duration
	- max posted days
- Sorting
	- match score, stipend, duration, posted days, company, title
- Source-level stats and partial-result handling

## Tech Stack

- Backend: FastAPI, requests, BeautifulSoup, PyPDF2
- Frontend: React (Vite), Tailwind CSS, axios
- Language: Python, JavaScript

## Project Structure

```text
.
|- main.py
|- requirements.txt
|- tools/
|  |- job_scraper.py
|  |- job_scraper_linkedin.py
|  |- job_scraper_naukri.py
|  |- job_scraper_indeed.py
|  |- job_scraper_wellfound.py
|  |- job_scraper_unstop.py
|  |- ranker.py
|  |- email_generator.py
|- internship-frontend/
	 |- package.json
	 |- src/
			|- App.jsx
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

## Setup

### 1) Backend Setup

```bash
cd "ai internship"
python -m venv venv
```

Windows PowerShell:

```powershell
venv\Scripts\Activate.ps1
```

Install backend dependencies:

```bash
pip install -r requirements.txt
pip install PyPDF2 beautifulsoup4
```

Run backend:

```bash
uvicorn main:app --reload
```

Backend runs on: `http://127.0.0.1:8000`

### 2) Frontend Setup

```bash
cd internship-frontend
npm install
npm run dev
```

Frontend runs on: `http://127.0.0.1:5173`

## API Endpoints

### `GET /`
Health check.

Response:

```json
{ "message": "Server is running 🚀" }
```

### `POST /upload-resume/`
Upload a PDF resume.

Form-data:
- `file`: PDF file

Response:

```json
{
	"structured_data": {
		"name": "Candidate Name",
		"education": "B.Tech ...",
		"skills": ["python", "analysis", "excel"]
	}
}
```

### `POST /auto-apply/`
Fetches, dedupes, filters, ranks, sorts and returns internship matches.

Query parameters:
- `keyword` (string, default: `finance`)
- `sources` (string, comma separated or `all`)
	- allowed: `internshala,linkedin,naukri,indeed,wellfound,unstop`
- `work_mode` (`remote|hybrid|on-site`)
- `location_contains` (string)
- `min_stipend` (int)
- `max_duration_months` (float)
- `max_posted_days` (int)
- `sort_by` (`match_score|stipend|duration|posted_days|company|title`)
- `sort_order` (`asc|desc`)
- `top_n` (int, default: `50`)

Example:

```text
POST /auto-apply/?keyword=data%20analyst&sources=all&work_mode=remote&min_stipend=10000&sort_by=match_score&sort_order=desc&top_n=50
```

Response (trimmed):

```json
{
	"total_jobs_found": 120,
	"total_jobs_after_dedupe": 87,
	"total_jobs_after_filters": 24,
	"source_stats": {
		"internshala": { "fetched": 20, "after_dedupe": 18, "after_filters": 7 }
	},
	"source_failures": [],
	"filters_applied": {
		"sources": ["internshala", "linkedin"],
		"sort_by": "match_score",
		"sort_order": "desc",
		"top_n": 50
	},
	"top_matches": [
		{
			"source": "internshala",
			"company": "ABC Pvt Ltd",
			"title": "Finance Intern",
			"match_score": 66.67,
			"job_meta": {
				"work_mode": "remote",
				"location_text": "Mumbai",
				"stipend_raw": "10,000/month"
			},
			"skills_detail": {
				"required_skills": ["excel", "analysis"],
				"matched_skills": ["analysis"],
				"missing_from_resume": ["excel"]
			}
		}
	]
}
```

## Frontend Usage Flow

1. Upload resume PDF
2. Confirm extracted skills
3. Enter keyword and select source/filter/sort options
4. Click `Find Internships`
5. Review results with:
	 - source badge
	 - match score
	 - metadata chips
	 - collapsible skills detail

## Known Limitations

- Some job sites are heavily dynamic and may return variable results in plain HTML scraping mode.
- CSS selectors can break when source websites change their UI.
- Resume parsing is keyword-based and can be improved with richer NLP/LLM extraction.

## Troubleshooting

- If `/auto-apply/` says `Upload resume first`, upload PDF at `/upload-resume/` first.
- If frontend cannot reach backend, ensure backend is running on `127.0.0.1:8000`.
- If Python imports fail in editor, select the correct virtual environment in VS Code.

## Deploy on Railway

This repository is configured for Railway backend deployment using:

- [Procfile](Procfile)
- [railway.toml](railway.toml)

### Steps

1. Push latest code to GitHub.
2. Open Railway and create a new project.
3. Select `Deploy from GitHub Repo` and choose this repository.
4. Railway detects Python via [requirements.txt](requirements.txt).
5. Deploy the service.

The app starts with:

```bash
uvicorn main:app --host 0.0.0.0 --port ${PORT}
```

### Required notes

- Health check path is `/`.
- Resume data is stored in-memory currently, so it resets on redeploy/restart.
- Some job sources are dynamic and may return varying results on hosted environments.
- Set Railway backend env var:
	- `FRONTEND_ORIGINS=https://<your-vercel-app>.vercel.app`
	- For multiple frontends, use comma-separated values.

### Frontend deployment

Deploy [internship-frontend](internship-frontend) as a separate Railway service (Node/Vite static build), or on Vercel/Netlify.
Then point frontend API calls to your Railway backend URL.

## Deploy Frontend on Vercel

1. Go to Vercel and click `Add New -> Project`.
2. Import this GitHub repository.
3. Set `Root Directory` to `internship-frontend`.
4. Framework preset: `Vite`.
5. Add environment variable:
	- `VITE_API_BASE_URL = https://<your-railway-backend>.up.railway.app`
6. Deploy.

Build settings (if asked manually):

- Build command: `npm run build`
- Output directory: `dist`

## Deploy Frontend on Netlify

1. Go to Netlify and click `Add new site -> Import an existing project`.
2. Connect GitHub and select this repo.
3. Set `Base directory` to `internship-frontend`.
4. Build command: `npm run build`
5. Publish directory: `dist`
6. Add environment variable:
	- `VITE_API_BASE_URL = https://<your-railway-backend>.up.railway.app`
7. Deploy site.

## Frontend Environment Variables

Use [internship-frontend/.env.example](internship-frontend/.env.example) as reference.

Local example:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Roadmap Ideas

- Switch selected sources to API-based adapters where possible
- Improve skill extraction and synonym handling
- Add persistent application tracker and saved searches
- Add CI checks for backend and frontend

## License

For internship/demo use. Add a formal license if publishing publicly.
