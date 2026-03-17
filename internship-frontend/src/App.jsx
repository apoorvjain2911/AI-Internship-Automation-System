import React, { useState } from "react";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [resumeResult, setResumeResult] = useState(null);
  const [jobsResult, setJobsResult] = useState(null);
  const [keyword, setKeyword] = useState("finance");
  const [loading, setLoading] = useState(false);
  const [jobLoading, setJobLoading] = useState(false);
  const [expandedJobDetails, setExpandedJobDetails] = useState({});
  const [workMode, setWorkMode] = useState("");
  const [locationContains, setLocationContains] = useState("");
  const [minStipend, setMinStipend] = useState("");
  const [maxDurationMonths, setMaxDurationMonths] = useState("");
  const [maxPostedDays, setMaxPostedDays] = useState("");
  const [sortBy, setSortBy] = useState("match_score");
  const [sortOrder, setSortOrder] = useState("desc");
  const [source, setSource] = useState("all");
  const [visibleJobs, setVisibleJobs] = useState(10);

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a resume first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);

      const response = await axios.post(
        `${API_BASE_URL}/upload-resume/`,
        formData
      );

      setResumeResult(response.data);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Error uploading resume.");
    } finally {
      setLoading(false);
    }
  };

  const handleAutoApply = async () => {
    try {
      setJobLoading(true);

      const params = new URLSearchParams();
      params.append("keyword", keyword);
      params.append("sort_by", sortBy);
      params.append("sort_order", sortOrder);
      params.append("top_n", "50");

      if (source && source !== "all") {
        params.append("sources", source);
      }

      if (workMode) params.append("work_mode", workMode);
      if (locationContains.trim()) {
        params.append("location_contains", locationContains.trim());
      }

      if (minStipend !== "") {
        const value = Number(minStipend);
        if (Number.isNaN(value) || value < 0) {
          alert("Minimum stipend must be a non-negative number.");
          setJobLoading(false);
          return;
        }
        params.append("min_stipend", String(value));
      }

      if (maxDurationMonths !== "") {
        const value = Number(maxDurationMonths);
        if (Number.isNaN(value) || value < 0) {
          alert("Maximum duration must be a non-negative number.");
          setJobLoading(false);
          return;
        }
        params.append("max_duration_months", String(value));
      }

      if (maxPostedDays !== "") {
        const value = Number(maxPostedDays);
        if (Number.isNaN(value) || value < 0) {
          alert("Posted-in-last-days must be a non-negative number.");
          setJobLoading(false);
          return;
        }
        params.append("max_posted_days", String(value));
      }

      const response = await axios.post(
        `${API_BASE_URL}/auto-apply/?${params.toString()}`
      );

      setJobsResult(response.data);
      setExpandedJobDetails({});
      setVisibleJobs(10);
    } catch (error) {
      console.error("Auto apply error:", error);
      alert("Error fetching internships.");
    } finally {
      setJobLoading(false);
    }
  };

  const getColor = (score) => {
    if (score >= 70) return "bg-green-500";
    if (score >= 40) return "bg-yellow-500";
    return "bg-red-500";
  };

  const toggleJobDetails = (index) => {
    setExpandedJobDetails((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const resetFilters = () => {
    setSource("all");
    setWorkMode("");
    setLocationContains("");
    setMinStipend("");
    setMaxDurationMonths("");
    setMaxPostedDays("");
    setSortBy("match_score");
    setSortOrder("desc");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white p-10">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8 text-indigo-400">
          AI Internship Automation System
        </h1>

        {/* Upload Section */}
        <div className="bg-slate-700 p-8 rounded-2xl shadow-xl mb-10">
          <input
            type="file"
            accept=".pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="mb-6 block w-full text-sm text-gray-300
            file:mr-4 file:py-2 file:px-4
            file:rounded-lg file:border-0
            file:text-sm file:font-semibold
            file:bg-indigo-600 file:text-white
            hover:file:bg-indigo-700"
          />

          <button
            onClick={handleUpload}
            className="w-full bg-indigo-600 hover:bg-indigo-700 py-3 rounded-xl font-semibold text-lg"
          >
            {loading ? "Analyzing..." : "Analyze Resume"}
          </button>
        </div>

        {resumeResult && resumeResult.structured_data && (
          <div className="space-y-6 mb-12">
            <div className="bg-slate-700 p-6 rounded-2xl shadow-xl">
              <h2 className="text-xl font-bold text-indigo-400">Candidate</h2>
              <p>{resumeResult.structured_data.name}</p>
            </div>

            <div className="bg-slate-700 p-6 rounded-2xl shadow-xl">
              <h2 className="text-xl font-bold text-indigo-400">Skills</h2>
              <div className="flex flex-wrap gap-3 mt-3">
                {resumeResult.structured_data.skills.map((skill, index) => (
                  <span
                    key={index}
                    className="bg-indigo-600 px-4 py-2 rounded-full text-sm font-semibold"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-slate-700 p-6 rounded-2xl shadow-xl">
              <h2 className="text-xl font-bold text-indigo-400 mb-4">
                🔎 Find Matching Internships
              </h2>

              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="w-full p-3 rounded-lg bg-slate-800 mb-4"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="w-full p-3 rounded-lg bg-slate-800"
                >
                  <option value="all">All Sources</option>
                  <option value="internshala">Internshala</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="naukri">Naukri</option>
                  <option value="indeed">Indeed</option>
                  <option value="wellfound">Wellfound</option>
                  <option value="unstop">Unstop</option>
                </select>

                <select
                  value={workMode}
                  onChange={(e) => setWorkMode(e.target.value)}
                  className="w-full p-3 rounded-lg bg-slate-800"
                >
                  <option value="">All Work Modes</option>
                  <option value="remote">Remote</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="on-site">On-site</option>
                </select>

                <input
                  type="text"
                  value={locationContains}
                  onChange={(e) => setLocationContains(e.target.value)}
                  placeholder="Location contains (e.g. Mumbai)"
                  className="w-full p-3 rounded-lg bg-slate-800"
                />

                <input
                  type="number"
                  min="0"
                  value={minStipend}
                  onChange={(e) => setMinStipend(e.target.value)}
                  placeholder="Minimum stipend"
                  className="w-full p-3 rounded-lg bg-slate-800"
                />

                <input
                  type="number"
                  min="0"
                  step="0.5"
                  value={maxDurationMonths}
                  onChange={(e) => setMaxDurationMonths(e.target.value)}
                  placeholder="Maximum duration (months)"
                  className="w-full p-3 rounded-lg bg-slate-800"
                />

                <input
                  type="number"
                  min="0"
                  value={maxPostedDays}
                  onChange={(e) => setMaxPostedDays(e.target.value)}
                  placeholder="Posted in last X days"
                  className="w-full p-3 rounded-lg bg-slate-800"
                />

                <div className="grid grid-cols-2 gap-3">
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="w-full p-3 rounded-lg bg-slate-800"
                  >
                    <option value="match_score">Sort: Match Score</option>
                    <option value="stipend">Sort: Stipend</option>
                    <option value="duration">Sort: Duration</option>
                    <option value="posted_days">Sort: Posted Days</option>
                    <option value="company">Sort: Company</option>
                    <option value="title">Sort: Title</option>
                  </select>

                  <select
                    value={sortOrder}
                    onChange={(e) => setSortOrder(e.target.value)}
                    className="w-full p-3 rounded-lg bg-slate-800"
                  >
                    <option value="desc">Desc</option>
                    <option value="asc">Asc</option>
                  </select>
                </div>
              </div>

              <button
                onClick={resetFilters}
                className="w-full bg-slate-800 hover:bg-slate-900 py-3 rounded-xl font-semibold text-sm mb-4"
              >
                Reset Filters
              </button>

              <button
                onClick={handleAutoApply}
                className="w-full bg-green-600 hover:bg-green-700 py-3 rounded-xl font-semibold text-lg"
              >
                {jobLoading ? "Searching..." : "Find Internships"}
              </button>
            </div>
          </div>
        )}

        {jobsResult && (
          <div className="space-y-4 mb-6">
            <div className="bg-slate-700 p-4 rounded-2xl shadow-xl">
              <p className="text-sm text-slate-200">
                Found {jobsResult.total_jobs_found ?? 0} jobs, {jobsResult.total_jobs_after_dedupe ?? 0} after dedupe, {jobsResult.total_jobs_after_filters ?? 0} after filters.
              </p>
              {jobsResult.source_stats && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {Object.entries(jobsResult.source_stats).map(([key, value]) => (
                    <span
                      key={key}
                      className="bg-slate-800 px-3 py-1 rounded-full text-xs"
                    >
                      {key}: {value.after_filters} / {value.fetched}
                    </span>
                  ))}
                </div>
              )}
              {jobsResult.message && (
                <p className="text-sm text-yellow-300 mt-2">{jobsResult.message}</p>
              )}
              {jobsResult.source_failures && jobsResult.source_failures.length > 0 && (
                <p className="text-sm text-amber-300 mt-2">
                  Partial results: {jobsResult.source_failures.map((item) => item.source).join(", ")} unavailable.
                </p>
              )}
            </div>
          </div>
        )}

        {jobsResult && jobsResult.top_matches && jobsResult.top_matches.length > 0 && (
          <div className="space-y-8">
            {jobsResult.top_matches.slice(0, visibleJobs).map((job, index) => (
              <div
                key={index}
                className="bg-slate-700 p-6 rounded-2xl shadow-xl"
              >
                <h3 className="text-2xl font-bold text-indigo-400">
                  {job.title}
                </h3>
                <p className="mb-2">{job.company}</p>

                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="bg-indigo-800 px-3 py-1 rounded-full text-xs uppercase tracking-wide">
                    Source: {job.source || "unknown"}
                  </span>
                  <span className="bg-slate-800 px-3 py-1 rounded-full text-xs">
                    Mode: {job.job_meta?.work_mode || "unknown"}
                  </span>
                  <span className="bg-slate-800 px-3 py-1 rounded-full text-xs">
                    Location: {job.job_meta?.location_text || "Not specified"}
                  </span>
                  <span className="bg-slate-800 px-3 py-1 rounded-full text-xs">
                    Stipend: {job.job_meta?.stipend_raw || "Not specified"}
                  </span>
                  <span className="bg-slate-800 px-3 py-1 rounded-full text-xs">
                    Duration: {job.job_meta?.duration_raw || "Not specified"}
                  </span>
                  <span className="bg-slate-800 px-3 py-1 rounded-full text-xs">
                    Posted: {job.job_meta?.posted_raw || "Not specified"}
                  </span>
                </div>

                <div className="mb-4">
                  <p className="mb-1 font-semibold">
                    Match Score: {job.match_score}%
                  </p>
                  <div className="w-full bg-slate-800 rounded-full h-4">
                    <div
                      className={`${getColor(
                        job.match_score
                      )} h-4 rounded-full`}
                      style={{ width: `${job.match_score}%` }}
                    ></div>
                  </div>
                </div>

                <div className="flex gap-4 mb-4">
                  <a
                    href={job.job_link}
                    target="_blank"
                    rel="noreferrer"
                    className="bg-indigo-600 px-4 py-2 rounded-lg"
                  >
                    View Job
                  </a>
                  <a
                    href={job.linkedin_search}
                    target="_blank"
                    rel="noreferrer"
                    className="bg-blue-600 px-4 py-2 rounded-lg"
                  >
                    LinkedIn
                  </a>
                </div>

                <button
                  onClick={() => toggleJobDetails(index)}
                  className="mb-4 bg-slate-800 hover:bg-slate-900 px-4 py-2 rounded-lg text-sm font-semibold"
                >
                  {expandedJobDetails[index]
                    ? "Hide Skills Detail"
                    : "Show Skills Detail"}
                </button>

                {expandedJobDetails[index] && (
                  <div className="bg-slate-800/70 rounded-xl p-4 space-y-4">
                    <h4 className="text-lg font-semibold text-indigo-300">
                      Skills Detail
                    </h4>

                    <div>
                      <p className="text-sm text-slate-300 mb-2">Required Skills</p>
                      <div className="flex flex-wrap gap-2">
                        {(job.skills_detail?.required_skills || []).length > 0 ? (
                          job.skills_detail.required_skills.map((skill, i) => (
                            <span
                              key={`req-${index}-${i}`}
                              className="bg-slate-600 px-3 py-1 rounded-full text-xs font-medium"
                            >
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-400 text-sm">No required skills found</span>
                        )}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-green-300 mb-2">Matched Skills</p>
                      <div className="flex flex-wrap gap-2">
                        {(job.skills_detail?.matched_skills || []).length > 0 ? (
                          job.skills_detail.matched_skills.map((skill, i) => (
                            <span
                              key={`match-${index}-${i}`}
                              className="bg-green-700 px-3 py-1 rounded-full text-xs font-medium"
                            >
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-400 text-sm">No skills matched</span>
                        )}
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-rose-300 mb-2">Missing From Resume</p>
                      <div className="flex flex-wrap gap-2">
                        {(job.skills_detail?.missing_from_resume || []).length > 0 ? (
                          job.skills_detail.missing_from_resume.map((skill, i) => (
                            <span
                              key={`miss-${index}-${i}`}
                              className="bg-rose-700 px-3 py-1 rounded-full text-xs font-medium"
                            >
                              {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-green-300 text-sm">No missing skills</span>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {jobsResult.top_matches.length > visibleJobs && (
              <button
                onClick={() => setVisibleJobs((prev) => prev + 10)}
                className="w-full bg-slate-700 hover:bg-slate-600 py-3 rounded-xl font-semibold"
              >
                Load More Jobs
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;