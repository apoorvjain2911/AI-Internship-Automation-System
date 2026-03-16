def generate_email(name, job):

    company = job["company"]
    title = job["title"]
    score = job["match_score"]
    matched = ", ".join(job.get("matched_skills", []))

    email = f"""
Subject: Application for {title} Internship

Dear {company} Hiring Team,

I am {name} and I am excited to apply for the {title} position.

My skills in {matched} align strongly with your requirements,
with a {score}% match to the job description.

I would love the opportunity to contribute to your team.

Looking forward to your response.

Best Regards,
{name}
"""

    return email.strip()