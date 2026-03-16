            response = requests.get(url, params=params)
            data = response.json()

            if data.get("results"):
                for job in data["results"]:
                    jobs.append(job.get("description", ""))

        except Exception:
            pass

    # If no API → generate 5 mock jobs
    if not jobs:
        mock_prompt = ChatPromptTemplate.from_template("""
        Generate 5 different realistic internship job descriptions for:
        {query}
        Separate each job clearly with "###".
        """)

        mock_chain = mock_prompt | llm
        result = mock_chain.invoke({"query": query})

        jobs = result.content.split("###")

    return {"job_list": jobs}


# -----------------------------
# 2️⃣ Resume Node
# -----------------------------

resume_prompt = ChatPromptTemplate.from_template("""
Extract:
- name
- education
- skills (as list)
- experience summary

Return JSON.
Resume:
{resume_text}
""")

resume_chain = resume_prompt | llm

def resume_node(state: InternshipState):
    result = resume_chain.invoke({
        "resume_text": state["resume_text"]
    })
    return {"resume_data": result.content}


# -----------------------------
# 3️⃣ Ranking Node (NEW)
# -----------------------------

ranking_prompt = ChatPromptTemplate.from_template("""
You are an AI recruiter.

Resume:
{resume_data}

Below are 5 job descriptions:

{job_list}

Select the BEST matching job for the resume.
Return ONLY the full selected job description.
""")

ranking_chain = ranking_prompt | llm

def ranking_node(state: InternshipState):
    result = ranking_chain.invoke({
        "resume_data": state["resume_data"],
        "job_list": state["job_list"]
    })

    return {"best_job_description": result.content}


# -----------------------------
# 4️⃣ Job Analysis Node
# -----------------------------

job_prompt = ChatPromptTemplate.from_template("""
Extract:
- role
- company
- required_skills (as list)

Return JSON.

Job Description:
{best_job_description}
""")

job_chain = job_prompt | llm

def job_node(state: InternshipState):
    result = job_chain.invoke({
        "best_job_description": state["best_job_description"]
    })

    return {"job_data": result.content}


# -----------------------------
# 5️⃣ Match Node
# -----------------------------

match_prompt = ChatPromptTemplate.from_template("""
Compare resume and job.

Resume:
{resume_data}

Job:
{job_data}

Return JSON:
- matched skills
- missing skills
- match_score (0-100)
- reasoning
""")

match_chain = match_prompt | llm

def match_node(state: InternshipState):
    result = match_chain.invoke({
        "resume_data": state["resume_data"],
        "job_data": state["job_data"]
    })
    return {"match_data": result.content}


# -----------------------------
# 6️⃣ Email Node
# -----------------------------

email_prompt = ChatPromptTemplate.from_template("""
Write a professional internship application email.

Resume:
{resume_data}

Job:
{job_data}

Match:
{match_data}

Tone: confident but humble.
Length: medium.
""")

email_chain = email_prompt | llm

def email_node(state: InternshipState):
    result = email_chain.invoke({
        "resume_data": state["resume_data"],
        "job_data": state["job_data"],
        "match_data": state["match_data"]
    })
    return {"email": result.content}


# -----------------------------
# Build Graph
# -----------------------------

workflow = StateGraph(InternshipState)

workflow.add_node("job_search", job_search_node)
workflow.add_node("resume", resume_node)
workflow.add_node("ranking", ranking_node)
workflow.add_node("job", job_node)
workflow.add_node("match", match_node)
workflow.add_node("email", email_node)

workflow.set_entry_point("job_search")

workflow.add_edge("job_search", "resume")
workflow.add_edge("resume", "ranking")
workflow.add_edge("ranking", "job")
workflow.add_edge("job", "match")
workflow.add_edge("match", "email")
workflow.add_edge("email", END)

graph = workflow.compile()