def rank_jobs(resume_skills, jobs):

    ranked = []

    for job in jobs:
        job_skills = job.get("skills_required", [])

        matched = list(set(resume_skills).intersection(set(job_skills)))

        score = round(
            (len(matched) / len(job_skills)) * 100,
            2
        ) if job_skills else 0

        job["match_score"] = score
        job["matched_skills"] = matched

        ranked.append(job)

    ranked.sort(key=lambda x: x["match_score"], reverse=True)

    return ranked