"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  MessageSquareCode,
  Sparkles,
  Send,
  CheckCircle,
  AlertTriangle,
  Lightbulb,
  Building,
  Target,
  FileCheck,
  RotateCcw,
  Trash2,
  Plus,
  AlertCircle,
  HelpCircle,
  ChevronRight,
  Award,
} from "lucide-react";
import {
  deleteInterviewPrep,
  evaluateInterviewAnswer,
  generateInterviewPrep,
  getInterviewPrep,
  listInterviewPreps,
  listMatches,
  InterviewPrep,
  InterviewPrepSummary,
  InterviewQuestion,
  MatchSummary,
} from "@/lib/api";

type QuestionTypeFilter = "ALL" | "TECHNICAL" | "BEHAVIORAL_STAR" | "GAP_DEFENSE";

export default function InterviewPage() {
  const [preps, setPreps] = useState<InterviewPrepSummary[]>([]);
  const [selectedPrep, setSelectedPrep] = useState<InterviewPrep | null>(null);
  const [selectedQuestion, setSelectedQuestion] = useState<InterviewQuestion | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Practice state
  const [practiceInput, setPracticeInput] = useState<string>("");

  // Filter state
  const [activeFilter, setActiveFilter] = useState<QuestionTypeFilter>("ALL");

  // New Prep Modal state
  const [showModal, setShowModal] = useState(false);
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const list = await listInterviewPreps();
      setPreps(list);
      if (list.length > 0) {
        const first = await getInterviewPrep(list[0].id);
        setSelectedPrep(first);
        if (first.questions.length > 0) {
          setSelectedQuestion(first.questions[0]);
          setPracticeInput(first.questions[0].practice_response || "");
        }
      } else {
        setSelectedPrep(null);
        setSelectedQuestion(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load interview preparations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openNewModal = async () => {
    setShowModal(true);
    try {
      const ms = await listMatches();
      setMatches(ms);
      if (ms.length > 0) {
        setSelectedMatchId(ms[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to fetch matching evaluations.");
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMatchId) return;

    try {
      setGenerating(true);
      setError(null);
      const created = await generateInterviewPrep(selectedMatchId);
      setShowModal(false);
      await loadData();
      setSelectedPrep(created);
      if (created.questions.length > 0) {
        setSelectedQuestion(created.questions[0]);
        setPracticeInput(created.questions[0].practice_response || "");
      }
    } catch (err: any) {
      setError(err.message || "Failed to generate interview preparation.");
    } finally {
      setGenerating(false);
    }
  };

  const handleSelectPrep = async (id: string) => {
    try {
      setError(null);
      const detail = await getInterviewPrep(id);
      setSelectedPrep(detail);
      if (detail.questions.length > 0) {
        setSelectedQuestion(detail.questions[0]);
        setPracticeInput(detail.questions[0].practice_response || "");
      }
    } catch (err: any) {
      setError(err.message || "Failed to load interview prep details.");
    }
  };

  const handleSelectQuestion = (q: InterviewQuestion) => {
    setSelectedQuestion(q);
    setPracticeInput(q.practice_response || "");
  };

  const handleEvaluate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedQuestion || practiceInput.trim().length < 10) return;

    try {
      setEvaluating(true);
      setError(null);
      const updated = await evaluateInterviewAnswer(selectedQuestion.id, practiceInput);
      setSelectedQuestion(updated);

      // Update question in active prep list
      if (selectedPrep) {
        setSelectedPrep({
          ...selectedPrep,
          questions: selectedPrep.questions.map((q) => (q.id === updated.id ? updated : q)),
        });
      }
    } catch (err: any) {
      setError(err.message || "Failed to evaluate answer.");
    } finally {
      setEvaluating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this interview preparation session?")) return;
    try {
      await deleteInterviewPrep(id);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to delete session.");
    }
  };

  // Filter questions
  const filteredQuestions = selectedPrep
    ? selectedPrep.questions.filter((q) => {
        if (activeFilter === "ALL") return true;
        return q.question_type === activeFilter;
      })
    : [];

  const getBadgeStyle = (type: string) => {
    switch (type) {
      case "TECHNICAL":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "BEHAVIORAL_STAR":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "GAP_DEFENSE":
        return "bg-amber-100 text-amber-800 border-amber-200";
      default:
        return "bg-slate-100 text-slate-800 border-slate-200";
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg well text-indigo-600">
              <MessageSquareCode className="w-5 h-5 text-indigo-600" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-soft-muted">
              Role-Specific Readiness & STAR Rubric
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-soft-text">
            Interview Intelligence & Practice Terminal
          </h1>
          <p className="text-sm text-soft-muted mt-0.5">
            Role-tailored technical probes, behavioral STAR questions, and gap-defense scenarios with live AI rubric evaluation.
          </p>
        </div>

        <button onClick={openNewModal} className="btn-primary flex items-center gap-2 self-start md:self-auto">
          <Plus className="w-4 h-4" />
          <span>New Interview Prep</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl well border-l-4 border-soft-orange text-soft-orange-text flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-xs font-bold underline">
            Dismiss
          </button>
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="surface p-6 rounded-2xl animate-pulse space-y-4">
            <div className="h-4 bg-slate-200 rounded w-1/2"></div>
            <div className="h-10 bg-slate-200 rounded"></div>
            <div className="h-10 bg-slate-200 rounded"></div>
          </div>
          <div className="md:col-span-2 surface p-6 rounded-2xl animate-pulse space-y-4">
            <div className="h-6 bg-slate-200 rounded w-1/3"></div>
            <div className="h-32 bg-slate-200 rounded"></div>
          </div>
        </div>
      ) : preps.length === 0 ? (
        /* Empty State */
        <div className="surface p-12 rounded-2xl text-center max-w-2xl mx-auto space-y-5">
          <div className="w-16 h-16 rounded-full well flex items-center justify-center mx-auto text-indigo-600">
            <MessageSquareCode className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-soft-text">No Interview Prep Sessions Found</h3>
            <p className="text-sm text-soft-muted">
              Select a matching evaluation to generate 10 tailored interview questions covering technical architecture, STAR behavioral leadership, and gap defenses.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button onClick={openNewModal} className="btn-primary flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              <span>Generate Interview Prep</span>
            </button>
            <Link href="/matches" className="btn-soft flex items-center gap-2">
              <span>View Match Reports</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      ) : (
        /* Main Workspace: Left Session List + Right Interactive Terminal */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Prep Sessions */}
          <div className="lg:col-span-4 space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-soft-muted px-1 flex items-center justify-between">
              <span>Interview Sessions ({preps.length})</span>
            </div>

            <div className="space-y-3">
              {preps.map((p) => {
                const isSelected = selectedPrep?.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => handleSelectPrep(p.id)}
                    className={`surface p-4 rounded-xl cursor-pointer transition-all duration-150 ${
                      isSelected
                        ? "border-2 border-indigo-600 shadow-md"
                        : "hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <h4 className="text-sm font-bold text-soft-text leading-tight">
                          {p.target_role_title}
                        </h4>
                        <div className="flex items-center gap-2 text-xs text-soft-muted">
                          {p.company_name && (
                            <span className="flex items-center gap-1 font-medium text-slate-700">
                              <Building className="w-3.5 h-3.5" />
                              {p.company_name}
                            </span>
                          )}
                          <span>•</span>
                          <span>{p.questions_count} questions</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Interactive Practice Terminal */}
          {selectedPrep && (
            <div className="lg:col-span-8 space-y-6">
              {/* Session Header Card */}
              <div className="surface p-6 rounded-2xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                        Interview Simulation
                      </span>
                      {selectedPrep.company_name && (
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                          {selectedPrep.company_name}
                        </span>
                      )}
                    </div>
                    <h2 className="text-xl font-bold text-soft-text mt-1">
                      {selectedPrep.target_role_title}
                    </h2>
                  </div>

                  <button
                    onClick={() => handleDelete(selectedPrep.id)}
                    className="btn-soft text-soft-orange hover:bg-orange-50 self-start sm:self-auto flex items-center gap-1.5 text-xs font-semibold py-2 px-3"
                    title="Delete Session"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete</span>
                  </button>
                </div>

                {/* Filter Tabs */}
                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-200">
                  <button
                    onClick={() => setActiveFilter("ALL")}
                    className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-all ${
                      activeFilter === "ALL"
                        ? "btn-primary text-white"
                        : "btn-soft text-soft-muted hover:text-soft-text"
                    }`}
                  >
                    All Questions ({selectedPrep.questions.length})
                  </button>
                  <button
                    onClick={() => setActiveFilter("TECHNICAL")}
                    className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-all ${
                      activeFilter === "TECHNICAL"
                        ? "bg-blue-600 text-white shadow-sm"
                        : "btn-soft text-soft-muted hover:text-soft-text"
                    }`}
                  >
                    Technical (4)
                  </button>
                  <button
                    onClick={() => setActiveFilter("BEHAVIORAL_STAR")}
                    className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-all ${
                      activeFilter === "BEHAVIORAL_STAR"
                        ? "bg-purple-600 text-white shadow-sm"
                        : "btn-soft text-soft-muted hover:text-soft-text"
                    }`}
                  >
                    Behavioral STAR (3)
                  </button>
                  <button
                    onClick={() => setActiveFilter("GAP_DEFENSE")}
                    className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-all ${
                      activeFilter === "GAP_DEFENSE"
                        ? "bg-amber-600 text-white shadow-sm"
                        : "btn-soft text-soft-muted hover:text-soft-text"
                    }`}
                  >
                    Gap Defense (3)
                  </button>
                </div>

                {/* Question Thumbnails Carousel/Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-1">
                  {filteredQuestions.map((q, idx) => {
                    const isCurrent = selectedQuestion?.id === q.id;
                    const hasAnswer = Boolean(q.practice_response);
                    const score = q.ai_feedback?.score;

                    return (
                      <button
                        key={q.id}
                        onClick={() => handleSelectQuestion(q)}
                        className={`p-2.5 rounded-xl text-left border transition-all text-xs flex flex-col justify-between ${
                          isCurrent
                            ? "well border-indigo-600 font-bold"
                            : "surface hover:border-slate-300"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] uppercase text-soft-muted font-bold">
                            Q{idx + 1}
                          </span>
                          {score !== undefined ? (
                            <span
                              className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full ${
                                score >= 80
                                  ? "bg-emerald-100 text-emerald-800"
                                  : score >= 60
                                  ? "bg-amber-100 text-amber-800"
                                  : "bg-red-100 text-red-800"
                              }`}
                            >
                              {Math.round(score)}%
                            </span>
                          ) : hasAnswer ? (
                            <span className="text-[9px] font-bold px-1.5 py-0.2 rounded-full bg-slate-100 text-slate-700">
                              Draft
                            </span>
                          ) : null}
                        </div>
                        <div className="line-clamp-1 text-[11px] text-soft-text">
                          {q.target_skill_or_gap || q.question_type}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Active Question Workspace */}
              {selectedQuestion && (
                <div className="surface p-6 rounded-2xl space-y-6">
                  {/* Question Banner */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${getBadgeStyle(
                          selectedQuestion.question_type
                        )}`}
                      >
                        {selectedQuestion.question_type.replace("_", " ")}
                      </span>
                      {selectedQuestion.target_skill_or_gap && (
                        <span className="text-xs font-semibold px-2.5 py-0.5 rounded-md well text-slate-700 flex items-center gap-1.5">
                          <Target className="w-3.5 h-3.5 text-indigo-600" />
                          <span>Focus: {selectedQuestion.target_skill_or_gap}</span>
                        </span>
                      )}
                    </div>

                    <h3 className="text-lg font-bold text-soft-text leading-snug">
                      {selectedQuestion.question_text}
                    </h3>
                  </div>

                  {/* STAR Guidelines Box */}
                  {selectedQuestion.star_guidelines &&
                    Object.keys(selectedQuestion.star_guidelines).length > 0 && (
                      <div className="well p-4 rounded-xl space-y-2 border-l-4 border-purple-500">
                        <div className="flex items-center gap-2 text-purple-800 font-bold text-xs uppercase tracking-wider">
                          <FileCheck className="w-4 h-4 text-purple-600" />
                          <span>STAR Response Blueprint</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                          {selectedQuestion.star_guidelines.situation && (
                            <div className="p-2 bg-white/70 rounded-lg">
                              <span className="font-bold text-purple-900 block mb-0.5">
                                Situation:
                              </span>
                              <span className="text-soft-muted">
                                {selectedQuestion.star_guidelines.situation}
                              </span>
                            </div>
                          )}
                          {selectedQuestion.star_guidelines.task && (
                            <div className="p-2 bg-white/70 rounded-lg">
                              <span className="font-bold text-purple-900 block mb-0.5">Task:</span>
                              <span className="text-soft-muted">
                                {selectedQuestion.star_guidelines.task}
                              </span>
                            </div>
                          )}
                          {selectedQuestion.star_guidelines.action && (
                            <div className="p-2 bg-white/70 rounded-lg">
                              <span className="font-bold text-purple-900 block mb-0.5">Action:</span>
                              <span className="text-soft-muted">
                                {selectedQuestion.star_guidelines.action}
                              </span>
                            </div>
                          )}
                          {selectedQuestion.star_guidelines.result && (
                            <div className="p-2 bg-white/70 rounded-lg">
                              <span className="font-bold text-purple-900 block mb-0.5">Result:</span>
                              <span className="text-soft-muted">
                                {selectedQuestion.star_guidelines.result}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                  {/* Evaluation Criteria */}
                  <div className="text-xs text-soft-muted flex items-start gap-2 bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <HelpCircle className="w-4 h-4 text-soft-blue flex-shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-slate-700">What interviewers look for: </span>
                      {selectedQuestion.evaluation_criteria}
                    </div>
                  </div>

                  {/* Candidate Practice Input Form */}
                  <form onSubmit={handleEvaluate} className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold uppercase tracking-wider text-soft-muted flex items-center gap-1.5">
                        <MessageSquareCode className="w-3.5 h-3.5" />
                        <span>Your Practice Response</span>
                      </label>
                      <span className="text-xs text-soft-muted">
                        {practiceInput.trim().split(/\s+/).filter(Boolean).length} words
                      </span>
                    </div>

                    <textarea
                      value={practiceInput}
                      onChange={(e) => setPracticeInput(e.target.value)}
                      placeholder="Structure your answer using the STAR method. Describe the situation, your specific role/task, decisive actions taken, and quantified business impact..."
                      rows={6}
                      className="w-full text-sm rounded-xl border border-slate-200 well p-4 focus:outline-hidden focus:border-indigo-600 font-sans leading-relaxed text-soft-text"
                    />

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[11px] text-soft-muted">
                        Evaluated locally via Ollama or bar-raiser heuristic rubrics. Zero paid LLM API calls.
                      </span>

                      <button
                        type="submit"
                        disabled={evaluating || practiceInput.trim().length < 10}
                        className="btn-primary text-xs py-2 px-4 flex items-center gap-2"
                      >
                        {evaluating ? (
                          <>
                            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            <span>Bar-Raiser Evaluating...</span>
                          </>
                        ) : (
                          <>
                            <Send className="w-3.5 h-3.5" />
                            <span>Evaluate Answer</span>
                          </>
                        )}
                      </button>
                    </div>
                  </form>

                  {/* AI Rubric Feedback Section */}
                  {selectedQuestion.ai_feedback && (
                    <div className="well p-5 rounded-2xl border-l-4 border-indigo-600 space-y-4 animate-in fade-in">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Award className="w-5 h-5 text-indigo-600" />
                          <h4 className="text-sm font-bold text-soft-text">
                            Bar-Raiser Rubric Evaluation
                          </h4>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-soft-muted font-medium">Readiness Score:</span>
                          <span
                            className={`text-sm font-bold px-2.5 py-0.5 rounded-full ${
                              selectedQuestion.ai_feedback.score >= 80
                                ? "bg-emerald-100 text-emerald-800"
                                : selectedQuestion.ai_feedback.score >= 60
                                ? "bg-amber-100 text-amber-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {Math.round(selectedQuestion.ai_feedback.score)} / 100
                          </span>
                        </div>
                      </div>

                      {/* Strengths */}
                      {selectedQuestion.ai_feedback.strengths &&
                        selectedQuestion.ai_feedback.strengths.length > 0 && (
                          <div className="space-y-1.5">
                            <div className="text-xs font-bold uppercase tracking-wider text-soft-green-text flex items-center gap-1.5">
                              <CheckCircle className="w-3.5 h-3.5" />
                              <span>Demonstrated Strengths</span>
                            </div>
                            <ul className="space-y-1 text-xs text-soft-text pl-5 list-disc font-medium">
                              {selectedQuestion.ai_feedback.strengths.map((str, sIdx) => (
                                <li key={sIdx}>{str}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                      {/* Improvements */}
                      {selectedQuestion.ai_feedback.improvements &&
                        selectedQuestion.ai_feedback.improvements.length > 0 && (
                          <div className="space-y-1.5">
                            <div className="text-xs font-bold uppercase tracking-wider text-soft-orange-text flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              <span>Areas for Improvement</span>
                            </div>
                            <ul className="space-y-1 text-xs text-soft-text pl-5 list-disc font-medium">
                              {selectedQuestion.ai_feedback.improvements.map((imp, iIdx) => (
                                <li key={iIdx}>{imp}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                      {/* Detailed Critique */}
                      {selectedQuestion.ai_feedback.critique && (
                        <div className="space-y-1 bg-white/80 p-3.5 rounded-xl border border-slate-200">
                          <div className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                            <Lightbulb className="w-3.5 h-3.5 text-indigo-600" />
                            <span>Qualitative Feedback</span>
                          </div>
                          <p className="text-xs text-soft-muted leading-relaxed">
                            {selectedQuestion.ai_feedback.critique}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Generate Interview Prep Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="surface p-6 rounded-2xl max-w-lg w-full space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b pb-3 border-slate-200">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg well text-indigo-600">
                  <MessageSquareCode className="w-5 h-5 text-indigo-600" />
                </span>
                <h3 className="text-lg font-bold text-soft-text">Generate Interview Preparation</h3>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-soft-muted hover:text-soft-text font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                  Select Matching Evaluation
                </label>
                {matches.length === 0 ? (
                  <div className="p-4 rounded-xl well text-xs text-soft-muted">
                    No matching evaluations found. Run a match analysis in the{" "}
                    <Link href="/matches" className="text-indigo-600 underline font-semibold">
                      Match Reports module
                    </Link>{" "}
                    first.
                  </div>
                ) : (
                  <select
                    value={selectedMatchId}
                    onChange={(e) => setSelectedMatchId(e.target.value)}
                    className="w-full text-sm rounded-xl border border-slate-200 well p-3 focus:outline-hidden focus:border-indigo-600 font-medium"
                    required
                  >
                    {matches.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.job_title} {m.company_name ? `at ${m.company_name}` : ""} (Match: {Math.round(m.overall_score)}%)
                      </option>
                    ))}
                  </select>
                )}
                <p className="text-xs text-soft-muted">
                  Generates 10 structured questions: 4 Technical Architecture, 3 Behavioral STAR, and 3 Gap-Defense.
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn-soft text-xs py-2 px-4"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating || matches.length === 0}
                  className="btn-primary text-xs py-2 px-4 flex items-center gap-2"
                >
                  {generating ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Generating Questions...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Generate Questions</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
