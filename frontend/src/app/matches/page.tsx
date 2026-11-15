"use client";

import React, { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Scale,
  Sparkles,
  Building,
  CheckCircle,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ShieldCheck,
  Trash2,
  Plus,
  BookOpen,
  ArrowRight,
  TrendingUp,
  FileText,
} from "lucide-react";
import {
  deleteMatch,
  evaluateMatch,
  getMatchDetail,
  listJobs,
  listMatches,
  listUserResumes,
  verifyMatchGap,
  JobDescriptionSummary,
  MatchEvaluation,
  MatchSummary,
  ResumeListItem,
  SkillGapItem,
} from "@/lib/api";

function MatchesContent() {
  const searchParams = useSearchParams();
  const queryJdId = searchParams.get("jd_id");

  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<MatchEvaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New Match Modal state
  const [showNewModal, setShowNewModal] = useState(false);
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [jobs, setJobs] = useState<JobDescriptionSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [selectedJdId, setSelectedJdId] = useState("");

  // Filter state for gaps
  const [gapFilter, setGapFilter] = useState<string>("all");

  // Quick Verification Modal state
  const [verifyingGap, setVerifyingGap] = useState<SkillGapItem | null>(null);
  const [verifyEvidence, setVerifyEvidence] = useState("");
  const [submittingVerification, setSubmittingVerification] = useState(false);

  useEffect(() => {
    loadMatches(queryJdId);
  }, [queryJdId]);

  async function loadMatches(targetJdId?: string | null) {
    try {
      setLoading(true);
      const data = await listMatches();
      setMatches(data);
      if (targetJdId) {
        const found = data.find((m) => m.jd_id === targetJdId);
        if (found) {
          const detail = await getMatchDetail(found.id);
          setSelectedMatch(detail);
          return;
        } else {
          openNewEvaluationModal(targetJdId);
          return;
        }
      }
      if (data.length > 0 && !selectedMatch) {
        const first = await getMatchDetail(data[0].id);
        setSelectedMatch(first);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load match evaluations");
    } finally {
      setLoading(false);
    }
  }

  async function openNewEvaluationModal(preselectedJdId?: string | null) {
    try {
      setError(null);
      const [resList, jobList] = await Promise.all([listUserResumes(), listJobs()]);
      setResumes(resList);
      setJobs(jobList);
      if (resList.length > 0) setSelectedResumeId(resList[0].id);
      if (preselectedJdId && jobList.some((j) => j.id === preselectedJdId)) {
        setSelectedJdId(preselectedJdId);
      } else if (jobList.length > 0) {
        setSelectedJdId(jobList[0].id);
      }
      setShowNewModal(true);
    } catch (err: any) {
      setError(err.message || "Failed to load options for evaluation");
    }
  }

  async function handleTriggerEvaluate(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedResumeId || !selectedJdId) {
      setError("Please select both a resume and a job description.");
      return;
    }

    try {
      setEvaluating(true);
      setError(null);
      const result = await evaluateMatch({
        resume_id: selectedResumeId,
        jd_id: selectedJdId,
      });

      setSelectedMatch(result);
      setShowNewModal(false);
      await loadMatches();
    } catch (err: any) {
      setError(err.message || "Failed to evaluate candidate-role match");
    } finally {
      setEvaluating(false);
    }
  }

  async function handleSelectMatch(id: string) {
    try {
      setError(null);
      const detail = await getMatchDetail(id);
      setSelectedMatch(detail);
    } catch (err: any) {
      setError(err.message || "Failed to load match details");
    }
  }

  async function handleDeleteMatch(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this match evaluation?")) return;

    try {
      await deleteMatch(id);
      if (selectedMatch?.id === id) {
        setSelectedMatch(null);
      }
      await loadMatches();
    } catch (err: any) {
      setError(err.message || "Failed to delete match");
    }
  }

  async function handleQuickVerify(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedMatch || !verifyingGap) return;

    try {
      setSubmittingVerification(true);
      const updated = await verifyMatchGap(selectedMatch.id, {
        gap_item_id: verifyingGap.id,
        has_experience: true,
        verification_evidence: verifyEvidence.trim() || undefined,
      });

      setSelectedMatch(updated);
      setVerifyingGap(null);
      setVerifyEvidence("");
      await loadMatches();
    } catch (err: any) {
      setError(err.message || "Failed to verify gap item");
    } finally {
      setSubmittingVerification(false);
    }
  }

  // Filtered gaps
  const gapItems = selectedMatch?.gap_items || [];
  const filteredGaps =
    gapFilter === "all"
      ? gapItems
      : gapFilter === "demonstrated"
      ? gapItems.filter((g) => g.status === "DEMONSTRATED")
      : gapFilter === "partial"
      ? gapItems.filter((g) => g.status === "PARTIAL")
      : gapFilter === "not_demonstrated"
      ? gapItems.filter((g) => g.status === "NOT_DEMONSTRATED")
      : gapFilter === "requires_verification"
      ? gapItems.filter((g) => g.status === "REQUIRES_VERIFICATION")
      : gapItems;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-soft-text flex items-center gap-2">
            <Scale className="w-6 h-6 text-soft-blue" />
            Candidate-Role Match Intelligence
          </h1>
          <p className="text-sm text-soft-muted mt-1">
            Hybrid scientific alignment engine combining BM25 lexical search, dense semantic similarity, and skill ontology coverage.
          </p>
        </div>

        <button
          onClick={() => openNewEvaluationModal()}
          className="btn-primary px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 cursor-pointer self-start sm:self-auto"
        >
          <Sparkles className="w-4 h-4" />
          Evaluate New Match
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-semibold text-xs underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Left = Saved Matches List, Right = Detailed Report */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="surface p-5 rounded-2xl space-y-3">
            <h2 className="text-sm font-bold text-soft-text">
              Match Evaluations ({matches.length})
            </h2>

            {loading ? (
              <div className="py-8 text-center text-xs text-soft-muted">
                Loading evaluations...
              </div>
            ) : matches.length === 0 ? (
              <div className="py-8 text-center text-xs text-soft-muted well rounded-xl p-4 space-y-2">
                <p>No evaluations yet.</p>
                <button
                  onClick={() => openNewEvaluationModal()}
                  className="text-soft-blue font-semibold underline text-xs cursor-pointer"
                >
                  Run your first evaluation
                </button>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[580px] overflow-y-auto pr-1">
                {matches.map((m) => {
                  const isSelected = selectedMatch?.id === m.id;
                  return (
                    <div
                      key={m.id}
                      onClick={() => handleSelectMatch(m.id)}
                      className={`p-3.5 rounded-xl transition-all cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? "well border-l-4 border-soft-blue"
                          : "surface hover:bg-white/40"
                      }`}
                    >
                      <div className="space-y-1 truncate pr-2">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-xs font-bold px-2 py-0.5 rounded-md ${
                              m.overall_score >= 80
                                ? "bg-emerald-50 text-soft-green-text"
                                : m.overall_score >= 65
                                ? "bg-blue-50 text-soft-blue"
                                : "bg-amber-50 text-soft-orange-text"
                            }`}
                          >
                            {Math.round(m.overall_score)}%
                          </span>
                          <p className="text-xs font-bold text-soft-text truncate">
                            {m.job_title}
                          </p>
                        </div>
                        <p className="text-[11px] text-soft-muted truncate">
                          {m.company_name || "Company"} • {m.rating_label}
                        </p>
                      </div>

                      <button
                        onClick={(e) => handleDeleteMatch(m.id, e)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors shrink-0"
                        title="Delete evaluation"
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

        {/* Right Column (8 cols): Detailed Report */}
        <div className="lg:col-span-8 space-y-6">
          {selectedMatch ? (
            <>
              {/* Top Banner: Score Dial & Multi-Factor Breakdown */}
              <div className="surface p-6 rounded-2xl space-y-6">
                <div className="flex flex-col md:flex-row items-center gap-8">
                  {/* Radial Dial / Score Card */}
                  <div className="flex flex-col items-center justify-center p-6 well rounded-2xl w-44 h-44 shrink-0 text-center border border-white/60">
                    <span className="text-[11px] font-bold uppercase text-soft-muted">
                      Overall Match
                    </span>
                    <span className="text-4xl font-extrabold text-soft-blue mt-1">
                      {Math.round(selectedMatch.overall_score)}%
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full mt-2 ${
                        selectedMatch.overall_score >= 80
                          ? "bg-emerald-50 text-soft-green-text border border-emerald-200"
                          : selectedMatch.overall_score >= 65
                          ? "bg-blue-50 text-soft-blue border border-blue-200"
                          : "bg-amber-50 text-soft-orange-text border border-amber-200"
                      }`}
                    >
                      {selectedMatch.rating_label}
                    </span>
                  </div>

                  {/* 5-Factor Score Meters */}
                  <div className="flex-1 space-y-3 w-full">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-soft-text">
                          {selectedMatch.job_title}
                        </h2>
                        {selectedMatch.company_name && (
                          <p className="text-xs font-semibold text-soft-blue flex items-center gap-1.5">
                            <Building className="w-3.5 h-3.5" />
                            {selectedMatch.company_name}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center gap-2 flex-wrap">
                        <Link
                          href={`/optimizer?match_id=${selectedMatch.id}&jd_id=${selectedMatch.jd_id}&resume_id=${selectedMatch.resume_id}`}
                          className="btn-primary px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm cursor-pointer"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          Open in Resume Studio
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                        <Link
                          href="/interview"
                          className="btn-soft px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer text-soft-text hover:text-soft-blue"
                        >
                          <BookOpen className="w-3.5 h-3.5 text-soft-blue" />
                          Interview Prep
                        </Link>
                        <Link
                          href="/learning"
                          className="btn-soft px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer text-soft-text hover:text-soft-blue"
                        >
                          <TrendingUp className="w-3.5 h-3.5 text-soft-green-text" />
                          Learning Plan
                        </Link>
                      </div>
                    </div>

                    <div className="space-y-2 pt-1 text-xs">
                      {/* Skill Match */}
                      <div>
                        <div className="flex justify-between font-medium text-soft-text mb-1">
                          <span>Skill Ontology Overlap (35%)</span>
                          <span className="font-bold">{selectedMatch.sub_scores.skill_match}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full well overflow-hidden">
                          <div
                            className="h-full bg-soft-blue rounded-full transition-all duration-500"
                            style={{ width: `${selectedMatch.sub_scores.skill_match}%` }}
                          />
                        </div>
                      </div>

                      {/* Semantic Similarity */}
                      <div>
                        <div className="flex justify-between font-medium text-soft-text mb-1">
                          <span>Semantic Vector Alignment (25%)</span>
                          <span className="font-bold">{selectedMatch.sub_scores.semantic_similarity}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full well overflow-hidden">
                          <div
                            className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                            style={{ width: `${selectedMatch.sub_scores.semantic_similarity}%` }}
                          />
                        </div>
                      </div>

                      {/* Lexical BM25 */}
                      <div>
                        <div className="flex justify-between font-medium text-soft-text mb-1">
                          <span>Lexical BM25 Grounding (15%)</span>
                          <span className="font-bold">{selectedMatch.sub_scores.lexical_bm25}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full well overflow-hidden">
                          <div
                            className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                            style={{ width: `${selectedMatch.sub_scores.lexical_bm25}%` }}
                          />
                        </div>
                      </div>

                      {/* Experience Depth */}
                      <div>
                        <div className="flex justify-between font-medium text-soft-text mb-1">
                          <span>Experience Threshold (15%)</span>
                          <span className="font-bold">{selectedMatch.sub_scores.experience_depth}%</span>
                        </div>
                        <div className="w-full h-2 rounded-full well overflow-hidden">
                          <div
                            className="h-full bg-amber-500 rounded-full transition-all duration-500"
                            style={{ width: `${selectedMatch.sub_scores.experience_depth}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recruiter Summary Narrative */}
                {selectedMatch.summary_analysis && (
                  <div className="well p-4 rounded-xl text-xs text-soft-text border border-white/80 space-y-1">
                    <p className="text-[10px] font-bold uppercase text-soft-muted flex items-center gap-1">
                      <TrendingUp className="w-3.5 h-3.5 text-soft-blue" />
                      Executive Match Analysis
                    </p>
                    <p className="leading-relaxed text-slate-700">
                      {selectedMatch.summary_analysis}
                    </p>
                  </div>
                )}
              </div>

              {/* Skill Gap Analysis Section */}
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h3 className="text-base font-bold text-soft-text">
                      Skill Gap Breakdown ({gapItems.length})
                    </h3>
                    <p className="text-xs text-soft-muted">
                      Categorized based on factual resume demonstration and ontology verification.
                    </p>
                  </div>

                  {/* Filter Tabs */}
                  <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                    {[
                      { key: "all", label: "All" },
                      { key: "demonstrated", label: "Demonstrated" },
                      { key: "partial", label: "Partial" },
                      { key: "not_demonstrated", label: "Missing" },
                      { key: "requires_verification", label: "Verify" },
                    ].map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setGapFilter(tab.key)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                          gapFilter === tab.key
                            ? "well text-soft-blue border border-soft-blue"
                            : "surface text-soft-muted hover:text-soft-text"
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Gap Cards */}
                <div className="space-y-3">
                  {filteredGaps.length === 0 ? (
                    <div className="surface p-8 text-center text-xs text-soft-muted rounded-2xl">
                      No requirements found in this filter category.
                    </div>
                  ) : (
                    filteredGaps.map((gap) => (
                      <div
                        key={gap.id}
                        className="surface p-4 rounded-2xl space-y-3 border border-white/60 transition-all hover:translate-y-[-1px]"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <p className="text-xs font-semibold text-soft-text leading-relaxed">
                              {gap.requirement_text}
                            </p>
                            <div className="flex items-center gap-2 text-[10px] text-soft-muted">
                              <span>{gap.is_mandatory ? "Must-Have (1.0)" : "Preferred (0.6)"}</span>
                              <span>•</span>
                              <span className="capitalize">{gap.category?.replace("_", " ")}</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                gap.status === "DEMONSTRATED"
                                  ? "bg-emerald-50 text-soft-green-text border border-emerald-200"
                                  : gap.status === "PARTIAL"
                                  ? "bg-amber-50 text-soft-orange-text border border-amber-200"
                                  : gap.status === "REQUIRES_VERIFICATION"
                                  ? "bg-blue-50 text-soft-blue border border-blue-200"
                                  : "bg-red-50 text-red-700 border border-red-200"
                              }`}
                            >
                              {gap.status.replace("_", " ")}
                            </span>

                            {gap.gap_severity === "CRITICAL" && (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-100 text-red-800">
                                Critical
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Evidence Snippet */}
                        {gap.evidence_snippet && (
                          <div className="well p-3 rounded-xl text-[11px] text-soft-text space-y-1">
                            <p className="text-[10px] font-bold uppercase text-soft-muted flex items-center gap-1">
                              <BookOpen className="w-3 h-3 text-soft-blue" />
                              Substantiated Evidence
                            </p>
                            <p className="italic text-slate-700 leading-relaxed">
                              &ldquo;{gap.evidence_snippet}&rdquo;
                            </p>
                          </div>
                        )}

                        {/* Suggested Action & Quick Verify Button */}
                        <div className="flex items-center justify-between pt-1 border-t border-slate-200/50 text-[11px]">
                          <p className="text-soft-muted truncate pr-2">
                            {gap.suggested_action}
                          </p>

                          {!gap.is_resolved && (
                            <button
                              onClick={() => {
                                setVerifyingGap(gap);
                                setVerifyEvidence("");
                              }}
                              className="btn-soft px-3 py-1 rounded-xl text-xs font-semibold text-soft-blue flex items-center gap-1 shrink-0 cursor-pointer"
                            >
                              <ShieldCheck className="w-3.5 h-3.5" />
                              Verify Experience
                            </button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="surface p-12 text-center rounded-2xl space-y-3">
              <Scale className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-sm font-bold text-soft-text">No Match Selected</h3>
              <p className="text-xs text-soft-muted max-w-sm mx-auto">
                Trigger a new candidate-role match or select an evaluated position from the left to inspect the explainable report.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* New Match Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="surface p-6 rounded-2xl max-w-lg w-full space-y-5 border border-white/80 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-soft-text flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-soft-blue" />
                Run Hybrid Candidate-Role Match
              </h3>
              <button
                onClick={() => setShowNewModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleTriggerEvaluate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Select Resume Document *
                </label>
                {resumes.length === 0 ? (
                  <p className="text-xs text-red-600 well p-3 rounded-xl">
                    No resumes uploaded. Please upload a resume in Resume Ingestion first.
                  </p>
                ) : (
                  <select
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    className="w-full text-xs rounded-xl well border border-white/60 p-3 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                    required
                  >
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.file_name} {r.is_master ? "(Master Profile)" : ""}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Select Target Job Description *
                </label>
                {jobs.length === 0 ? (
                  <p className="text-xs text-red-600 well p-3 rounded-xl">
                    No jobs analyzed. Please analyze a job posting in JD Intelligence first.
                  </p>
                ) : (
                  <select
                    value={selectedJdId}
                    onChange={(e) => setSelectedJdId(e.target.value)}
                    className="w-full text-xs rounded-xl well border border-white/60 p-3 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                    required
                  >
                    {jobs.map((j) => (
                      <option key={j.id} value={j.id}>
                        {j.job_title} ({j.company_name || "Company"}) • {j.requirements_count} reqs
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="btn-soft px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={evaluating || resumes.length === 0 || jobs.length === 0}
                  className="btn-primary px-5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {evaluating ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Evaluating Alignment...
                    </>
                  ) : (
                    <>
                      <Scale className="w-4 h-4" />
                      Compute Hybrid Score
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Quick Verification Modal */}
      {verifyingGap && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="surface p-6 rounded-2xl max-w-md w-full space-y-4 border border-white/80 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-soft-text flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-soft-blue" />
                Verify Competency Experience
              </h3>
              <button
                onClick={() => setVerifyingGap(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="well p-3 rounded-xl text-xs text-soft-text">
              <p className="font-semibold text-soft-muted text-[10px] uppercase">
                Requirement Statement
              </p>
              <p className="mt-0.5">{verifyingGap.requirement_text}</p>
            </div>

            <form onSubmit={handleQuickVerify} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Practical Evidence / Demonstration Notes (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="e.g. Built automated CI/CD pipelines with Kubernetes and Helm at previous company..."
                  value={verifyEvidence}
                  onChange={(e) => setVerifyEvidence(e.target.value)}
                  className="w-full text-xs rounded-xl well border border-white/60 p-3 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue resize-none"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setVerifyingGap(null)}
                  className="btn-soft px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingVerification}
                  className="btn-primary px-5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {submittingVerification ? "Updating Score..." : "Confirm & Recalculate"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function MatchesPage() {
  return (
    <Suspense
      fallback={
        <div className="surface p-12 text-center text-xs text-soft-muted rounded-2xl">
          Loading candidate-role match intelligence...
        </div>
      }
    >
      <MatchesContent />
    </Suspense>
  );
}
