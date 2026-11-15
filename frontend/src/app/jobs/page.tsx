"use client";

import React, { useEffect, useState } from "react";
import {
  FileSearch,
  Building,
  MapPin,
  DollarSign,
  Briefcase,
  Trash2,
  CheckCircle,
  Clock,
  Sparkles,
  ArrowRight,
  Filter,
} from "lucide-react";
import {
  analyzeJob,
  deleteJob,
  getJobDetail,
  listJobs,
  JobDescription,
  JobDescriptionSummary,
} from "@/lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobDescriptionSummary[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobDescription | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form inputs
  const [rawText, setRawText] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [activeTab, setActiveTab] = useState<"mandatory" | "preferred" | "all">("mandatory");

  useEffect(() => {
    loadJobs();
  }, []);

  async function loadJobs() {
    try {
      setLoading(true);
      const data = await listJobs();
      setJobs(data);
      if (data.length > 0 && !selectedJob) {
        const first = await getJobDetail(data[0].id);
        setSelectedJob(first);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }

  async function handleAnalyze(e: React.FormEvent) {
    e.preventDefault();
    if (!rawText.trim() || rawText.trim().length < 20) {
      setError("Please provide a valid job description (at least 20 characters).");
      return;
    }

    try {
      setAnalyzing(true);
      setError(null);
      const newJob = await analyzeJob({
        raw_text: rawText,
        job_title: jobTitle.trim() || undefined,
        company_name: companyName.trim() || undefined,
      });

      setSelectedJob(newJob);
      setRawText("");
      setJobTitle("");
      setCompanyName("");
      await loadJobs();
    } catch (err: any) {
      setError(err.message || "Failed to analyze job description");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleSelectJob(id: string) {
    try {
      setError(null);
      const detail = await getJobDetail(id);
      setSelectedJob(detail);
    } catch (err: any) {
      setError(err.message || "Failed to load job details");
    }
  }

  async function handleDeleteJob(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this job description?")) return;

    try {
      await deleteJob(id);
      if (selectedJob?.id === id) {
        setSelectedJob(null);
      }
      await loadJobs();
    } catch (err: any) {
      setError(err.message || "Failed to delete job");
    }
  }

  const mandatoryReqs = selectedJob?.requirements.filter((r) => r.is_mandatory) || [];
  const preferredReqs = selectedJob?.requirements.filter((r) => !r.is_mandatory) || [];
  const displayedReqs =
    activeTab === "mandatory"
      ? mandatoryReqs
      : activeTab === "preferred"
      ? preferredReqs
      : selectedJob?.requirements || [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-soft-text flex items-center gap-2">
          <FileSearch className="w-6 h-6 text-soft-blue" />
          JD Intelligence Engine
        </h1>
        <p className="text-sm text-soft-muted mt-1">
          Deconstruct job descriptions into mandatory vs. preferred requirements, extract experience thresholds, and map canonical skills.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-semibold text-xs underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Left = Input & Saved Jobs, Right = Decomposed Intelligence View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Analyze Opportunity Form */}
          <div className="surface p-6 rounded-2xl space-y-4">
            <h2 className="text-base font-bold text-soft-text flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-soft-blue" />
              Analyze New Job Description
            </h2>

            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Job Title (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Senior Machine Learning Engineer"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full text-xs rounded-xl well border border-white/60 px-3.5 py-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Company / Organization (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. DeepMind, Stripe, Google"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full text-xs rounded-xl well border border-white/60 px-3.5 py-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Job Description Text *
                </label>
                <textarea
                  rows={8}
                  placeholder="Paste the full job posting text here (responsibilities, required qualifications, nice-to-haves)..."
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  className="w-full text-xs rounded-xl well border border-white/60 p-3.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue resize-none"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={analyzing}
                className="w-full btn-primary py-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {analyzing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Extracting & Classifying Requirements...
                  </>
                ) : (
                  <>
                    <FileSearch className="w-4 h-4" />
                    Analyze Opportunity
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Saved Job Opportunities Library */}
          <div className="surface p-6 rounded-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-soft-text">
                Saved Positions ({jobs.length})
              </h2>
            </div>

            {loading ? (
              <div className="py-8 text-center text-xs text-soft-muted">
                Loading saved positions...
              </div>
            ) : jobs.length === 0 ? (
              <div className="py-8 text-center text-xs text-soft-muted well rounded-xl p-4">
                No jobs analyzed yet. Paste a job description above to get started.
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[420px] overflow-y-auto pr-1">
                {jobs.map((job) => {
                  const isSelected = selectedJob?.id === job.id;
                  return (
                    <div
                      key={job.id}
                      onClick={() => handleSelectJob(job.id)}
                      className={`p-3.5 rounded-xl transition-all cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? "well border-l-4 border-soft-blue"
                          : "surface hover:bg-white/40"
                      }`}
                    >
                      <div className="space-y-1 truncate pr-2">
                        <p className="text-xs font-bold text-soft-text truncate">
                          {job.job_title}
                        </p>
                        <div className="flex items-center gap-2 text-[11px] text-soft-muted">
                          {job.company_name && (
                            <span className="truncate">{job.company_name}</span>
                          )}
                          {job.work_mode && (
                            <span className="bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded text-[10px]">
                              {job.work_mode}
                            </span>
                          )}
                          <span>• {job.requirements_count} reqs</span>
                        </div>
                      </div>

                      <button
                        onClick={(e) => handleDeleteJob(job.id, e)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                        title="Delete position"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column (7 cols): Decomposed Intelligence View */}
        <div className="lg:col-span-7 space-y-6">
          {selectedJob ? (
            <>
              {/* Job Metadata Banner */}
              <div className="surface p-6 rounded-2xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-bold text-soft-text">
                      {selectedJob.job_title}
                    </h2>
                    {selectedJob.company_name && (
                      <p className="text-xs font-semibold text-soft-blue flex items-center gap-1.5 mt-0.5">
                        <Building className="w-3.5 h-3.5" />
                        {selectedJob.company_name}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    {selectedJob.seniority_level && (
                      <span className="text-xs font-bold px-2.5 py-1 rounded-xl well text-soft-text border border-white/60">
                        {selectedJob.seniority_level}
                      </span>
                    )}
                    {selectedJob.work_mode && (
                      <span className="text-xs font-bold px-2.5 py-1 rounded-xl bg-blue-50 text-soft-blue border border-blue-200">
                        {selectedJob.work_mode}
                      </span>
                    )}
                  </div>
                </div>

                {/* Sub-meta tags */}
                <div className="flex items-center gap-4 text-xs text-soft-muted pt-2 border-t border-slate-200/50 flex-wrap">
                  {selectedJob.location && (
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {selectedJob.location}
                    </span>
                  )}
                  {selectedJob.salary_range && (
                    <span className="flex items-center gap-1 text-soft-green-text font-semibold">
                      <DollarSign className="w-3.5 h-3.5" />
                      {selectedJob.salary_range}
                    </span>
                  )}
                  <span className="flex items-center gap-1 text-slate-400">
                    <Clock className="w-3.5 h-3.5" />
                    Analyzed {new Date(selectedJob.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {/* Requirements Taxonomy Filter Tabs */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab("mandatory")}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    activeTab === "mandatory"
                      ? "well text-soft-blue border-b-2 border-soft-blue"
                      : "surface text-soft-muted hover:text-soft-text"
                  }`}
                >
                  Mandatory ({mandatoryReqs.length})
                </button>
                <button
                  onClick={() => setActiveTab("preferred")}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    activeTab === "preferred"
                      ? "well text-soft-blue border-b-2 border-soft-blue"
                      : "surface text-soft-muted hover:text-soft-text"
                  }`}
                >
                  Preferred ({preferredReqs.length})
                </button>
                <button
                  onClick={() => setActiveTab("all")}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    activeTab === "all"
                      ? "well text-soft-blue border-b-2 border-soft-blue"
                      : "surface text-soft-muted hover:text-soft-text"
                  }`}
                >
                  All ({selectedJob.requirements.length})
                </button>
              </div>

              {/* Requirement Cards */}
              <div className="space-y-3">
                {displayedReqs.length === 0 ? (
                  <div className="surface p-8 text-center text-xs text-soft-muted rounded-2xl">
                    No requirements found in this category.
                  </div>
                ) : (
                  displayedReqs.map((req) => (
                    <div
                      key={req.id}
                      className="surface p-4 rounded-2xl space-y-2 border border-white/60 transition-all hover:translate-y-[-1px]"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-xs text-soft-text leading-relaxed font-medium">
                          {req.requirement_text}
                        </p>
                        <span
                          className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            req.is_mandatory
                              ? "bg-red-50 text-red-700 border border-red-200"
                              : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          }`}
                        >
                          {req.is_mandatory ? "Must Have (1.0)" : "Preferred (0.6)"}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 pt-1 flex-wrap text-[11px]">
                        <span className="well px-2 py-0.5 rounded-lg text-soft-muted capitalize">
                          {req.category.replace("_", " ")}
                        </span>

                        {req.min_years_experience && (
                          <span className="well px-2 py-0.5 rounded-lg text-soft-blue font-semibold">
                            {req.min_years_experience}+ Yrs Exp
                          </span>
                        )}

                        {req.canonical_skill_name && (
                          <span className="bg-blue-50 text-soft-blue border border-blue-200 px-2 py-0.5 rounded-lg font-semibold">
                            Concept: {req.canonical_skill_name}
                          </span>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="surface p-12 text-center rounded-2xl space-y-3">
              <FileSearch className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-sm font-bold text-soft-text">No Opportunity Selected</h3>
              <p className="text-xs text-soft-muted max-w-sm mx-auto">
                Paste a job description on the left or select an analyzed job to inspect decomposed requirements and ontology skills.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
