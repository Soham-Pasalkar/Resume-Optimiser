"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  GraduationCap,
  Sparkles,
  Clock,
  CheckCircle2,
  Circle,
  ExternalLink,
  BookOpen,
  FolderGit2,
  Trash2,
  Plus,
  AlertCircle,
  ChevronRight,
  TrendingUp,
  Award,
  ShieldCheck,
} from "lucide-react";
import {
  deleteRoadmap,
  generateRoadmap,
  getRoadmap,
  listMatches,
  listRoadmaps,
  submitMilestoneEvidence,
  toggleMilestone,
  LearningMilestone,
  LearningRoadmap,
  LearningRoadmapSummary,
  MatchSummary,
} from "@/lib/api";

export default function LearningPage() {
  const [roadmaps, setRoadmaps] = useState<LearningRoadmapSummary[]>([]);
  const [selectedRoadmap, setSelectedRoadmap] = useState<LearningRoadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New Roadmap Modal
  const [showModal, setShowModal] = useState(false);
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState("");

  // Submit Evidence Modal
  const [evidenceMilestone, setEvidenceMilestone] = useState<LearningMilestone | null>(null);
  const [evidenceText, setEvidenceText] = useState("");
  const [evidenceGithub, setEvidenceGithub] = useState("");
  const [evidenceDemo, setEvidenceDemo] = useState("");
  const [evidenceTests, setEvidenceTests] = useState("");
  const [submittingEvidence, setSubmittingEvidence] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const list = await listRoadmaps();
      setRoadmaps(list);
      if (list.length > 0) {
        const first = await getRoadmap(list[0].id);
        setSelectedRoadmap(first);
      } else {
        setSelectedRoadmap(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load learning roadmaps.");
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
      const created = await generateRoadmap(selectedMatchId);
      setShowModal(false);
      await loadData();
      setSelectedRoadmap(created);
    } catch (err: any) {
      setError(err.message || "Failed to generate learning roadmap.");
    } finally {
      setGenerating(false);
    }
  };

  const handleSelectRoadmap = async (id: string) => {
    try {
      setError(null);
      const detail = await getRoadmap(id);
      setSelectedRoadmap(detail);
    } catch (err: any) {
      setError(err.message || "Failed to load roadmap details.");
    }
  };

  const handleToggleMilestone = async (milestone: LearningMilestone) => {
    if (!selectedRoadmap) return;
    const newStatus = !milestone.is_completed;

    // Optimistic update
    setSelectedRoadmap({
      ...selectedRoadmap,
      milestones: selectedRoadmap.milestones.map((m) =>
        m.id === milestone.id ? { ...m, is_completed: newStatus } : m
      ),
      completed_count: newStatus
        ? selectedRoadmap.completed_count + 1
        : Math.max(0, selectedRoadmap.completed_count - 1),
    });

    try {
      await toggleMilestone(milestone.id, newStatus);
      // Refresh summary item in the list
      const updatedList = await listRoadmaps();
      setRoadmaps(updatedList);
    } catch (err: any) {
      setError(err.message || "Failed to update milestone status.");
      // Rollback on failure
      const reverted = await getRoadmap(selectedRoadmap.id);
      setSelectedRoadmap(reverted);
    }
  };

  const handleSubmitEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!evidenceMilestone || !evidenceText.trim()) return;

    try {
      setSubmittingEvidence(true);
      await submitMilestoneEvidence(evidenceMilestone.id, {
        evidence_text: evidenceText.trim(),
        github_url: evidenceGithub.trim() || undefined,
        demo_url: evidenceDemo.trim() || undefined,
        test_results: evidenceTests.trim() || undefined,
      });
      setEvidenceMilestone(null);
      setEvidenceText("");
      setEvidenceGithub("");
      setEvidenceDemo("");
      setEvidenceTests("");
      if (selectedRoadmap) {
        const refreshed = await getRoadmap(selectedRoadmap.id);
        setSelectedRoadmap(refreshed);
      }
      const updatedList = await listRoadmaps();
      setRoadmaps(updatedList);
    } catch (err: any) {
      setError(err.message || "Failed to submit project deliverable evidence.");
    } finally {
      setSubmittingEvidence(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this learning roadmap?")) return;
    try {
      await deleteRoadmap(id);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to delete roadmap.");
    }
  };

  const percentComplete =
    selectedRoadmap && selectedRoadmap.total_milestones > 0
      ? Math.round((selectedRoadmap.completed_count / selectedRoadmap.total_milestones) * 100)
      : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg well text-soft-blue">
              <GraduationCap className="w-5 h-5 text-soft-blue" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-soft-muted">
              Career Competency Development
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-soft-text">
            Personalized Learning Roadmaps
          </h1>
          <p className="text-sm text-soft-muted mt-0.5">
            Targeted skill milestone curricula and practical portfolio project briefs synthesized from gap analyses.
          </p>
        </div>

        <button onClick={openNewModal} className="btn-primary flex items-center gap-2 self-start md:self-auto">
          <Plus className="w-4 h-4" />
          <span>New Learning Roadmap</span>
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
      ) : roadmaps.length === 0 ? (
        /* Empty State */
        <div className="surface p-12 rounded-2xl text-center max-w-2xl mx-auto space-y-5">
          <div className="w-16 h-16 rounded-full well flex items-center justify-center mx-auto text-soft-blue">
            <GraduationCap className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-soft-text">No Learning Roadmaps Generated Yet</h3>
            <p className="text-sm text-soft-muted">
              Run a match evaluation between your resume and a target job description, then generate a tailored milestone roadmap to bridge identified gaps.
            </p>
          </div>
          <div className="flex items-center justify-center gap-3 pt-2">
            <button onClick={openNewModal} className="btn-primary flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              <span>Generate Roadmap</span>
            </button>
            <Link href="/matches" className="btn-soft flex items-center gap-2">
              <span>View Match Reports</span>
              <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      ) : (
        /* Main Workspace: Left Nav + Detail */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Roadmap Selector */}
          <div className="lg:col-span-4 space-y-3">
            <div className="text-xs font-bold uppercase tracking-wider text-soft-muted px-1 flex items-center justify-between">
              <span>Your Roadmaps ({roadmaps.length})</span>
            </div>

            <div className="space-y-3">
              {roadmaps.map((r) => {
                const isSelected = selectedRoadmap?.id === r.id;
                return (
                  <div
                    key={r.id}
                    onClick={() => handleSelectRoadmap(r.id)}
                    className={`surface p-4 rounded-xl cursor-pointer transition-all duration-150 ${
                      isSelected
                        ? "border-2 border-soft-blue shadow-md"
                        : "hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <h4 className="text-sm font-bold text-soft-text leading-tight">
                          {r.target_role_title}
                        </h4>
                        <div className="flex items-center gap-3 text-xs text-soft-muted">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5 text-soft-blue" />
                            {r.estimated_total_hours}h estimated
                          </span>
                          <span>•</span>
                          <span>{r.milestones_count} milestones</span>
                        </div>
                      </div>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          r.status === "COMPLETED"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {r.status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Active Roadmap Detail */}
          {selectedRoadmap && (
            <div className="lg:col-span-8 space-y-6">
              {/* Roadmap Header Card */}
              <div className="surface p-6 rounded-2xl space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-soft-blue">
                        Active Curriculum
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          selectedRoadmap.status === "COMPLETED"
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {selectedRoadmap.status}
                      </span>
                    </div>
                    <h2 className="text-xl font-bold text-soft-text mt-1">
                      {selectedRoadmap.target_role_title}
                    </h2>
                  </div>

                  <button
                    onClick={() => handleDelete(selectedRoadmap.id)}
                    className="btn-soft text-soft-orange hover:bg-orange-50 self-start sm:self-auto flex items-center gap-1.5 text-xs font-semibold py-2 px-3"
                    title="Delete Roadmap"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete</span>
                  </button>
                </div>

                {/* Progress Metric Wells */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="well p-4 rounded-xl flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-soft-blue/10 text-soft-blue">
                      <Clock className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xs text-soft-muted font-medium">Estimated Time</div>
                      <div className="text-lg font-bold text-soft-text">
                        {selectedRoadmap.estimated_total_hours} Hours
                      </div>
                    </div>
                  </div>

                  <div className="well p-4 rounded-xl flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-emerald-50 text-soft-green">
                      <Award className="w-5 h-5 text-soft-green" />
                    </div>
                    <div>
                      <div className="text-xs text-soft-muted font-medium">Completed</div>
                      <div className="text-lg font-bold text-soft-text">
                        {selectedRoadmap.completed_count} / {selectedRoadmap.total_milestones}
                      </div>
                    </div>
                  </div>

                  <div className="well p-4 rounded-xl flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-600">
                      <TrendingUp className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-xs text-soft-muted font-medium">Progress</div>
                      <div className="text-lg font-bold text-soft-text">{percentComplete}%</div>
                    </div>
                  </div>
                </div>

                {/* Horizontal Progress Bar */}
                <div className="space-y-1.5">
                  <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
                    <div
                      className="bg-soft-blue h-full transition-all duration-300 rounded-full"
                      style={{ width: `${percentComplete}%` }}
                    />
                  </div>
                  <div className="text-[11px] text-soft-muted flex justify-between">
                    <span>Curriculum Completion</span>
                    <span className="font-semibold text-soft-text">{percentComplete}% Done</span>
                  </div>
                </div>
              </div>

              {/* Milestone Cards Sequence */}
              <div className="space-y-4">
                <div className="text-xs font-bold uppercase tracking-wider text-soft-muted px-1">
                  Sequential Learning Milestones ({selectedRoadmap.milestones.length})
                </div>

                {selectedRoadmap.milestones.map((m, idx) => (
                  <div
                    key={m.id}
                    className={`surface p-5 rounded-2xl transition-all duration-150 space-y-4 ${
                      m.is_completed ? "bg-slate-50/60 border-l-4 border-soft-green" : ""
                    }`}
                  >
                    {/* Milestone Header */}
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <button
                          onClick={() => handleToggleMilestone(m)}
                          className="mt-0.5 text-soft-muted hover:text-soft-blue transition-colors flex-shrink-0"
                          title={m.is_completed ? "Mark incomplete" : "Mark completed"}
                        >
                          {m.is_completed ? (
                            <CheckCircle2 className="w-6 h-6 text-soft-green" />
                          ) : (
                            <Circle className="w-6 h-6 text-slate-300 hover:text-soft-blue" />
                          )}
                        </button>

                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-bold text-soft-blue px-2 py-0.5 rounded-md well">
                              Step {m.sequence_order || idx + 1}
                            </span>
                            <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                              {m.skill_name}
                            </span>
                            {m.is_completed && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-soft-green-text">
                                Completed
                              </span>
                            )}
                          </div>
                          <h3
                            className={`text-base font-bold text-soft-text ${
                              m.is_completed ? "line-through text-soft-muted" : ""
                            }`}
                          >
                            {m.milestone_title}
                          </h3>
                        </div>
                      </div>
                    </div>

                    {/* Description & Why It Matters */}
                    <div className="pl-9 space-y-2">
                      {m.why_it_matters && (
                        <div className="well p-3 rounded-xl border border-white/60 text-xs text-soft-text space-y-0.5">
                          <span className="text-[10px] font-bold uppercase text-soft-blue flex items-center gap-1">
                            <TrendingUp className="w-3 h-3" />
                            Why It Matters for Target Role
                          </span>
                          <p className="italic text-slate-700">{m.why_it_matters}</p>
                        </div>
                      )}
                      <p className="text-xs text-soft-muted leading-relaxed">
                        {m.description}
                      </p>
                    </div>

                    {/* Prerequisites & Objectives */}
                    {((m.prerequisites && m.prerequisites.length > 0) || (m.learning_objectives && m.learning_objectives.length > 0)) && (
                      <div className="pl-9 grid grid-cols-1 md:grid-cols-2 gap-3">
                        {m.prerequisites && m.prerequisites.length > 0 && (
                          <div className="well p-3 rounded-xl text-xs space-y-1">
                            <span className="text-[10px] font-bold uppercase text-soft-muted">Prerequisites</span>
                            <ul className="list-disc pl-4 space-y-0.5 text-slate-600 text-[11px]">
                              {m.prerequisites.map((p, pIdx) => (
                                <li key={pIdx}>{p}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {m.learning_objectives && m.learning_objectives.length > 0 && (
                          <div className="well p-3 rounded-xl text-xs space-y-1">
                            <span className="text-[10px] font-bold uppercase text-soft-muted">Learning Objectives</span>
                            <ul className="list-disc pl-4 space-y-0.5 text-slate-600 text-[11px]">
                              {m.learning_objectives.map((obj, oIdx) => (
                                <li key={oIdx}>{obj}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Curated Resources */}
                    {m.curated_resources && m.curated_resources.length > 0 && (
                      <div className="pl-9 space-y-2">
                        <div className="text-xs font-bold uppercase tracking-wider text-soft-muted flex items-center gap-1.5">
                          <BookOpen className="w-3.5 h-3.5" />
                          <span>Curated Authoritative Material</span>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {m.curated_resources.map((res, rIdx) => (
                            <a
                              key={rIdx}
                              href={res.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs font-semibold text-soft-blue well hover:bg-white px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors border border-transparent hover:border-soft-blue/20"
                            >
                              <span>{res.title}</span>
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-50 text-blue-700">
                                {res.type}
                              </span>
                              <ExternalLink className="w-3 h-3 text-soft-muted" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Practical Drills */}
                    {m.practical_exercises && m.practical_exercises.length > 0 && (
                      <div className="pl-9 space-y-1.5">
                        <span className="text-[10px] font-bold uppercase text-soft-muted tracking-wider block">
                          Hands-On Drills
                        </span>
                        <div className="space-y-1">
                          {m.practical_exercises.map((ex, exIdx) => (
                            <div key={exIdx} className="well p-2 rounded-lg text-xs text-slate-700">
                              {ex}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Practical Portfolio Project Brief */}
                    {m.practical_project_brief && (
                      <div className="pl-9 space-y-2">
                        <div className="well p-4 rounded-xl border-l-4 border-indigo-500 space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-indigo-700 font-bold text-xs uppercase tracking-wider">
                              <FolderGit2 className="w-4 h-4 text-indigo-600" />
                              <span>Practical Portfolio Deliverable Brief</span>
                            </div>
                            <span className="text-[10px] font-bold text-slate-500">
                              ~{m.estimated_hours || 15} Hours
                            </span>
                          </div>
                          <p className="text-xs text-soft-text leading-relaxed font-medium">
                            {m.practical_project_brief}
                          </p>

                          {m.expected_deliverables && m.expected_deliverables.length > 0 && (
                            <div className="pt-1 border-t border-slate-200/50 space-y-0.5">
                              <span className="text-[10px] font-bold uppercase text-indigo-700">Deliverables</span>
                              <ul className="list-disc pl-4 text-[11px] text-slate-600">
                                {m.expected_deliverables.map((del, dIdx) => (
                                  <li key={dIdx}>{del}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {m.verification_criteria && m.verification_criteria.length > 0 && (
                            <div className="pt-1 border-t border-slate-200/50 space-y-0.5">
                              <span className="text-[10px] font-bold uppercase text-emerald-700">Verification Criteria</span>
                              <ul className="list-disc pl-4 text-[11px] text-slate-600">
                                {m.verification_criteria.map((crit, cIdx) => (
                                  <li key={cIdx}>{crit}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>

                        {/* Evidence Records and Verification Status */}
                        {m.verification_status === "VERIFIED" || (m.evidence_verified && m.completed_evidence) ? (
                          <div className="surface p-3.5 rounded-xl border border-emerald-300 bg-emerald-50/20 space-y-1.5 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-emerald-800 flex items-center gap-1.5">
                                <Award className="w-4 h-4 text-emerald-600" />
                                Verified Deliverable & Synchronized Competency
                              </span>
                              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                                Verified in Profile
                              </span>
                            </div>
                            <p className="text-slate-700">{m.completed_evidence?.evidence_text}</p>
                            {m.completed_evidence?.github_url && (
                              <a
                                href={m.completed_evidence.github_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-soft-blue hover:underline flex items-center gap-1 font-semibold"
                              >
                                <ExternalLink className="w-3 h-3" />
                                Repository: {m.completed_evidence.github_url}
                              </a>
                            )}
                          </div>
                        ) : m.verification_status === "PENDING_REVIEW" || (m.completed_evidence && !m.evidence_verified) ? (
                          <div className="surface p-3.5 rounded-xl border border-amber-300 bg-amber-50/20 space-y-1.5 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-amber-800 flex items-center gap-1.5">
                                <Clock className="w-4 h-4 text-amber-600" />
                                Deliverable Submitted — Awaiting Review
                              </span>
                              <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                                Pending Verification
                              </span>
                            </div>
                            <p className="text-slate-700">{m.completed_evidence?.evidence_text}</p>
                            {m.completed_evidence?.github_url && (
                              <a
                                href={m.completed_evidence.github_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-amber-800 hover:underline flex items-center gap-1 font-semibold"
                              >
                                <ExternalLink className="w-3 h-3" />
                                Repository: {m.completed_evidence.github_url}
                              </a>
                            )}
                          </div>
                        ) : (
                          <div className="flex justify-end pt-1">
                            <button
                              onClick={() => {
                                setEvidenceMilestone(m);
                                setEvidenceText("");
                                setEvidenceGithub("");
                                setEvidenceDemo("");
                                setEvidenceTests("");
                              }}
                              className="btn-primary px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                            >
                              <ShieldCheck className="w-3.5 h-3.5" />
                              <span>Submit Deliverable for Review</span>
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Generate Roadmap Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="surface p-6 rounded-2xl max-w-lg w-full space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b pb-3 border-slate-200">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg well text-soft-blue">
                  <GraduationCap className="w-5 h-5 text-soft-blue" />
                </span>
                <h3 className="text-lg font-bold text-soft-text">Generate Learning Roadmap</h3>
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
                    <Link href="/matches" className="text-soft-blue underline font-semibold">
                      Match Reports module
                    </Link>{" "}
                    first.
                  </div>
                ) : (
                  <select
                    value={selectedMatchId}
                    onChange={(e) => setSelectedMatchId(e.target.value)}
                    className="w-full text-sm rounded-xl border border-slate-200 well p-3 focus:outline-hidden focus:border-soft-blue font-medium"
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
                  Synthesizes unaddressed gaps from this match report into practical, sequenced learning milestones.
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
                      <span>Synthesizing Curriculum...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Generate Roadmap</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Submit Evidence Modal */}
      {evidenceMilestone && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="surface p-6 rounded-2xl max-w-lg w-full space-y-4 animate-in fade-in zoom-in-95 border border-white/80 shadow-2xl">
            <div className="flex items-center justify-between border-b pb-3 border-slate-200">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg well text-emerald-600">
                  <Award className="w-5 h-5 text-emerald-600" />
                </span>
                <div>
                  <h3 className="text-base font-bold text-soft-text">
                    Submit Deliverable & Verify Competency
                  </h3>
                  <p className="text-xs text-soft-muted">
                    {evidenceMilestone.skill_name} • Step {evidenceMilestone.sequence_order}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setEvidenceMilestone(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="well p-3 rounded-xl text-xs text-slate-700 space-y-1">
              <span className="text-[10px] font-bold uppercase text-soft-muted">Expected Project Brief</span>
              <p className="italic">{evidenceMilestone.practical_project_brief}</p>
            </div>

            <form onSubmit={handleSubmitEvidence} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Deliverable Summary & Outcomes *
                </label>
                <textarea
                  rows={3}
                  value={evidenceText}
                  onChange={(e) => setEvidenceText(e.target.value)}
                  placeholder="Describe your implementation, architecture, and outcomes verifying this skill..."
                  className="w-full text-xs rounded-xl well border border-white/60 p-3 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue resize-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  GitHub Repository URL (Optional)
                </label>
                <input
                  type="url"
                  value={evidenceGithub}
                  onChange={(e) => setEvidenceGithub(e.target.value)}
                  placeholder="https://github.com/username/project"
                  className="w-full text-xs rounded-xl well border border-white/60 p-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                    Live Demo Link
                  </label>
                  <input
                    type="url"
                    value={evidenceDemo}
                    onChange={(e) => setEvidenceDemo(e.target.value)}
                    placeholder="https://demo.app"
                    className="w-full text-xs rounded-xl well border border-white/60 p-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                    Test Assertions
                  </label>
                  <input
                    type="text"
                    value={evidenceTests}
                    onChange={(e) => setEvidenceTests(e.target.value)}
                    placeholder="100% test coverage"
                    className="w-full text-xs rounded-xl well border border-white/60 p-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                  />
                </div>
              </div>

              <p className="text-[10px] text-soft-muted">
                Submissions are recorded with full provenance and entered into review before formal competency verification in your profile.
              </p>

              <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setEvidenceMilestone(null)}
                  className="btn-soft text-xs py-2 px-4 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingEvidence || !evidenceText.trim()}
                  className="btn-primary text-xs py-2 px-4 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {submittingEvidence ? "Verifying..." : "Submit & Sync to Profile"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
