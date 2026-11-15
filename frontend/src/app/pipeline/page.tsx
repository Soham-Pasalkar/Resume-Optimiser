"use client";

import React, { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Kanban,
  Table,
  Plus,
  Scale,
  Building,
  MapPin,
  DollarSign,
  Calendar,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Trash2,
  Edit,
  Sparkles,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  Search,
  Filter,
  Check,
  Eye,
  Tag,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import {
  compareOpportunities,
  createApplication,
  deleteApplication,
  getApplication,
  listApplications,
  listJobs,
  listMatches,
  listTailoredResumes,
  updateApplication,
  updateApplicationStage,
  JobApplication,
  JobApplicationCreatePayload,
  JobApplicationSummary,
  JobDescriptionSummary,
  MatchSummary,
  OpportunityComparisonResponse,
  TailoredResumeSummary,
} from "@/lib/api";

const STAGES = [
  { key: "WISHLIST", label: "Wishlist", color: "border-slate-300 text-slate-700 bg-slate-50" },
  { key: "APPLIED", label: "Applied", color: "border-blue-400 text-blue-700 bg-blue-50" },
  { key: "SCREENING", label: "Screening", color: "border-indigo-400 text-indigo-700 bg-indigo-50" },
  { key: "INTERVIEWING", label: "Interviewing", color: "border-purple-400 text-purple-700 bg-purple-50" },
  { key: "OFFER", label: "Offer", color: "border-emerald-400 text-emerald-700 bg-emerald-50" },
  { key: "REJECTED", label: "Archived", color: "border-rose-400 text-rose-700 bg-rose-50" },
];

function PipelineContent() {
  const searchParams = useSearchParams();
  const queryJdId = searchParams.get("jd_id");
  const queryMatchId = searchParams.get("match_id");

  const [applications, setApplications] = useState<JobApplicationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"KANBAN" | "TABLE">("KANBAN");
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Detail Drawer state
  const [selectedApp, setSelectedApp] = useState<JobApplication | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Multi-select for Opportunity Comparison
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<OpportunityComparisonResponse | null>(null);
  const [comparing, setComparing] = useState(false);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  // New Application Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [jobs, setJobs] = useState<JobDescriptionSummary[]>([]);
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [tailoredResumes, setTailoredResumes] = useState<TailoredResumeSummary[]>([]);

  const [newAppForm, setNewAppForm] = useState<JobApplicationCreatePayload>({
    company_name: "",
    job_title: "",
    location: "",
    stage: "WISHLIST",
    priority: "MEDIUM",
    salary_range: "",
    job_url: "",
    notes: "",
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const list = await listApplications(undefined, searchQuery || undefined);
      setApplications(list);
    } catch (err: any) {
      setError(err.message || "Failed to load applications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    if (queryJdId || queryMatchId) {
      openCreateModal(queryJdId, queryMatchId);
    }
  }, [searchQuery, queryJdId, queryMatchId]);

  const openCreateModal = async (preselectJdId?: string | null, preselectMatchId?: string | null) => {
    setShowCreateModal(true);
    try {
      const [jList, mList, rList] = await Promise.all([
        listJobs().catch(() => []),
        listMatches().catch(() => []),
        listTailoredResumes().catch(() => []),
      ]);
      setJobs(jList);
      setMatches(mList);
      setTailoredResumes(rList);

      if (preselectJdId) {
        const jd = jList.find((j) => j.id === preselectJdId);
        if (jd) {
          setNewAppForm((prev) => ({
            ...prev,
            job_description_id: preselectJdId,
            company_name: jd.company_name || prev.company_name,
            job_title: jd.job_title || prev.job_title,
          }));
        }
      }
      if (preselectMatchId) {
        setNewAppForm((prev) => ({
          ...prev,
          match_evaluation_id: preselectMatchId,
        }));
      }
    } catch {
      // Ignored
    }
  };

  const handleSelectJD = (jdId: string) => {
    const jd = jobs.find((j) => j.id === jdId);
    if (jd) {
      setNewAppForm((prev) => ({
        ...prev,
        job_description_id: jdId,
        company_name: jd.company_name || prev.company_name,
        job_title: jd.job_title || prev.job_title,
      }));
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAppForm.company_name || !newAppForm.job_title) return;

    try {
      setCreating(true);
      setError(null);
      await createApplication(newAppForm);
      setShowCreateModal(false);
      setNewAppForm({
        company_name: "",
        job_title: "",
        location: "",
        stage: "WISHLIST",
        priority: "MEDIUM",
        salary_range: "",
        job_url: "",
        notes: "",
      });
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create application.");
    } finally {
      setCreating(false);
    }
  };

  const handleStageMove = async (appId: string, currentStage: string, direction: "prev" | "next") => {
    const stageKeys = STAGES.map((s) => s.key);
    const currIdx = stageKeys.indexOf(currentStage);
    const targetIdx = direction === "next" ? currIdx + 1 : currIdx - 1;

    if (targetIdx < 0 || targetIdx >= stageKeys.length) return;
    const targetStage = stageKeys[targetIdx];

    // Optimistic UI update
    setApplications((prev) =>
      prev.map((a) => (a.id === appId ? { ...a, stage: targetStage } : a))
    );

    try {
      await updateApplicationStage(appId, targetStage);
    } catch (err: any) {
      setError(err.message || "Failed to update stage.");
      await loadData();
    }
  };

  const handleOpenDetail = async (id: string) => {
    try {
      setLoadingDetail(true);
      const detail = await getApplication(id);
      setSelectedApp(detail);
    } catch (err: any) {
      setError(err.message || "Failed to load application details.");
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this job application?")) return;
    try {
      await deleteApplication(id);
      if (selectedApp?.id === id) setSelectedApp(null);
      setSelectedIds((prev) => prev.filter((item) => item !== id));
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to delete application.");
    }
  };

  const toggleSelectForCompare = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleRunComparison = async () => {
    if (selectedIds.length < 2) {
      alert("Please select at least 2 applications to compare.");
      return;
    }
    try {
      setComparing(true);
      setError(null);
      const res = await compareOpportunities(selectedIds);
      setComparisonResult(res);
      setShowComparisonModal(true);
    } catch (err: any) {
      setError(err.message || "Failed to compare opportunities.");
    } finally {
      setComparing(false);
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p.toUpperCase()) {
      case "HIGH":
        return "bg-rose-100 text-rose-800 border-rose-200";
      case "MEDIUM":
        return "bg-amber-100 text-amber-800 border-amber-200";
      case "LOW":
        return "bg-slate-100 text-slate-700 border-slate-200";
      default:
        return "bg-slate-100 text-slate-700";
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg well text-soft-blue">
              <Kanban className="w-5 h-5 text-soft-blue" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-soft-muted">
              Pipeline & Application Intelligence
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-soft-text">
            Job Application Pipeline
          </h1>
          <p className="text-sm text-soft-muted mt-0.5">
            Track recruitment stages, manage tailored ATS resumes, and benchmark qualification metrics side-by-side.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          {/* View Toggle */}
          <div className="well p-1 rounded-xl flex items-center gap-1">
            <button
              onClick={() => setViewMode("KANBAN")}
              className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                viewMode === "KANBAN" ? "bg-white text-soft-blue shadow-xs" : "text-soft-muted hover:text-soft-text"
              }`}
            >
              <Kanban className="w-3.5 h-3.5" />
              <span>Board</span>
            </button>
            <button
              onClick={() => setViewMode("TABLE")}
              className={`p-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                viewMode === "TABLE" ? "bg-white text-soft-blue shadow-xs" : "text-soft-muted hover:text-soft-text"
              }`}
            >
              <Table className="w-3.5 h-3.5" />
              <span>Table</span>
            </button>
          </div>

          {/* Compare Opportunities Button */}
          {selectedIds.length >= 2 && (
            <button
              onClick={handleRunComparison}
              disabled={comparing}
              className="btn-soft border-indigo-200 text-indigo-700 hover:bg-indigo-50 text-xs py-2 px-3 flex items-center gap-1.5 font-bold animate-in fade-in"
            >
              <Scale className="w-4 h-4 text-indigo-600" />
              <span>Compare ({selectedIds.length})</span>
            </button>
          )}

          <button onClick={() => openCreateModal()} className="btn-primary flex items-center gap-2 text-xs py-2 px-3.5">
            <Plus className="w-4 h-4" />
            <span>New Application</span>
          </button>
        </div>
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

      {/* Search & Selection Bar */}
      <div className="surface p-3.5 rounded-xl flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-soft-muted ml-2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by company or job title..."
            className="w-full text-xs bg-transparent border-none focus:outline-hidden text-soft-text font-medium"
          />
        </div>

        <div className="flex items-center gap-3 text-xs text-soft-muted">
          <span>
            Total: <strong className="text-soft-text">{applications.length}</strong> applications
          </span>
          {selectedIds.length > 0 && (
            <button
              onClick={() => setSelectedIds([])}
              className="text-soft-blue underline font-semibold"
            >
              Clear selection ({selectedIds.length})
            </button>
          )}
        </div>
      </div>

      {/* Main Board Workspace */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4 animate-pulse">
          {STAGES.map((s) => (
            <div key={s.key} className="surface h-96 rounded-2xl p-4 space-y-3">
              <div className="h-4 bg-slate-200 rounded w-1/2"></div>
              <div className="h-24 bg-slate-200 rounded"></div>
              <div className="h-24 bg-slate-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : applications.length === 0 ? (
        /* Empty State */
        <div className="surface p-12 rounded-2xl text-center max-w-xl mx-auto space-y-4">
          <div className="w-16 h-16 rounded-full well flex items-center justify-center mx-auto text-soft-blue">
            <Kanban className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-soft-text">Your Pipeline is Currently Empty</h3>
            <p className="text-sm text-soft-muted">
              Add your first target opportunity, attach tailored resumes and match reports, and manage interviews effortlessly.
            </p>
          </div>
          <button onClick={() => openCreateModal()} className="btn-primary inline-flex items-center gap-2 mt-2">
            <Plus className="w-4 h-4" />
            <span>Add First Application</span>
          </button>
        </div>
      ) : viewMode === "KANBAN" ? (
        /* Kanban Board View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 items-start">
          {STAGES.map((stage) => {
            const stageApps = applications.filter((a) => a.stage === stage.key);

            return (
              <div key={stage.key} className="space-y-3">
                {/* Stage Column Header */}
                <div className={`p-3 rounded-xl border flex items-center justify-between ${stage.color}`}>
                  <span className="text-xs font-bold uppercase tracking-wider">{stage.label}</span>
                  <span className="text-xs font-extrabold px-2 py-0.5 rounded-full bg-white/80 shadow-xs">
                    {stageApps.length}
                  </span>
                </div>

                {/* Cards Container */}
                <div className="space-y-3 min-h-[150px]">
                  {stageApps.map((app) => {
                    const isSelected = selectedIds.includes(app.id);

                    return (
                      <div
                        key={app.id}
                        className={`surface p-4 rounded-xl space-y-3 transition-all duration-150 relative ${
                          isSelected ? "border-2 border-indigo-600 shadow-md" : "hover:border-slate-300"
                        }`}
                      >
                        {/* Card Header & Checkbox */}
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-start gap-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSelectForCompare(app.id)}
                              className="mt-0.5 rounded text-indigo-600 focus:ring-0 cursor-pointer"
                              title="Select to compare"
                            />
                            <div>
                              <span className="text-xs font-semibold text-soft-muted block leading-none">
                                {app.company_name}
                              </span>
                              <h4
                                onClick={() => handleOpenDetail(app.id)}
                                className="text-sm font-bold text-soft-text hover:text-soft-blue cursor-pointer mt-1 line-clamp-2"
                              >
                                {app.job_title}
                              </h4>
                            </div>
                          </div>

                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md border ${getPriorityBadge(
                              app.priority
                            )}`}
                          >
                            {app.priority}
                          </span>
                        </div>

                        {/* Badges / Metrics */}
                        <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                          {app.match_score !== null && app.match_score !== undefined && (
                            <span className="px-2 py-0.5 rounded-md bg-emerald-50 text-soft-green font-bold flex items-center gap-1">
                              <Sparkles className="w-3 h-3" />
                              {Math.round(app.match_score)}%
                            </span>
                          )}
                          {app.salary_range && (
                            <span className="px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium truncate max-w-[120px]">
                              {app.salary_range}
                            </span>
                          )}
                        </div>

                        {/* Kanban Stage Advance Arrows */}
                        <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-soft-muted">
                          <button
                            onClick={() => handleStageMove(app.id, app.stage, "prev")}
                            disabled={stage.key === "WISHLIST"}
                            className="p-1 rounded-md hover:bg-slate-100 disabled:opacity-20 disabled:hover:bg-transparent"
                            title="Move back"
                          >
                            <ChevronLeft className="w-3.5 h-3.5" />
                          </button>

                          <button
                            onClick={() => handleOpenDetail(app.id)}
                            className="text-[11px] font-semibold text-soft-blue hover:underline"
                          >
                            View
                          </button>

                          <button
                            onClick={() => handleStageMove(app.id, app.stage, "next")}
                            disabled={stage.key === "REJECTED"}
                            className="p-1 rounded-md hover:bg-slate-100 disabled:opacity-20 disabled:hover:bg-transparent"
                            title="Advance stage"
                          >
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Table View */
        <div className="surface rounded-2xl overflow-hidden border border-slate-200">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-soft-muted font-bold uppercase tracking-wider">
                  <th className="p-3 w-10">Select</th>
                  <th className="p-3">Company & Role</th>
                  <th className="p-3">Stage</th>
                  <th className="p-3">Priority</th>
                  <th className="p-3">Match Score</th>
                  <th className="p-3">Salary</th>
                  <th className="p-3">Location</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {applications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="p-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(app.id)}
                        onChange={() => toggleSelectForCompare(app.id)}
                        className="rounded text-indigo-600 focus:ring-0 cursor-pointer"
                      />
                    </td>
                    <td className="p-3">
                      <div className="font-bold text-soft-text text-sm">{app.company_name}</div>
                      <div className="text-soft-muted">{app.job_title}</div>
                    </td>
                    <td className="p-3">
                      <span className="font-semibold px-2 py-0.5 rounded-full well text-soft-blue">
                        {app.stage}
                      </span>
                    </td>
                    <td className="p-3">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getPriorityBadge(
                          app.priority
                        )}`}
                      >
                        {app.priority}
                      </span>
                    </td>
                    <td className="p-3 font-bold text-soft-green">
                      {app.match_score !== null && app.match_score !== undefined
                        ? `${Math.round(app.match_score)}%`
                        : "—"}
                    </td>
                    <td className="p-3 text-soft-text font-medium">{app.salary_range || "—"}</td>
                    <td className="p-3 text-soft-muted">{app.location || "—"}</td>
                    <td className="p-3 text-right space-x-2">
                      <button
                        onClick={() => handleOpenDetail(app.id)}
                        className="text-soft-blue hover:underline font-semibold"
                      >
                        Details
                      </button>
                      <button
                        onClick={() => handleDelete(app.id)}
                        className="text-soft-orange hover:underline font-semibold"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Application Detail Drawer / Modal */}
      {selectedApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="surface p-6 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto space-y-6 animate-in fade-in zoom-in-95">
            <div className="flex items-start justify-between border-b pb-4 border-slate-200">
              <div>
                <span className="text-xs font-bold text-soft-muted uppercase tracking-wider">
                  {selectedApp.company_name}
                </span>
                <h3 className="text-xl font-bold text-soft-text mt-0.5">{selectedApp.job_title}</h3>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full well text-soft-blue">
                    Stage: {selectedApp.stage}
                  </span>
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-md border ${getPriorityBadge(
                      selectedApp.priority
                    )}`}
                  >
                    Priority: {selectedApp.priority}
                  </span>
                  {selectedApp.match_score !== null && selectedApp.match_score !== undefined && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800">
                      Match: {Math.round(selectedApp.match_score)}%
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleDelete(selectedApp.id)}
                  className="btn-soft text-soft-orange hover:bg-orange-50 text-xs p-2"
                  title="Delete Application"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setSelectedApp(null)}
                  className="text-soft-muted hover:text-soft-text font-bold text-sm ml-2"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Quick Details Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="well p-3 rounded-xl space-y-1">
                <span className="text-soft-muted font-medium flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5" /> Location
                </span>
                <p className="font-bold text-soft-text">{selectedApp.location || "Not specified"}</p>
              </div>

              <div className="well p-3 rounded-xl space-y-1">
                <span className="text-soft-muted font-medium flex items-center gap-1.5">
                  <DollarSign className="w-3.5 h-3.5" /> Salary Range
                </span>
                <p className="font-bold text-soft-text">{selectedApp.salary_range || "Not specified"}</p>
              </div>

              {selectedApp.job_url && (
                <div className="well p-3 rounded-xl space-y-1 sm:col-span-2">
                  <span className="text-soft-muted font-medium flex items-center gap-1.5">
                    <ExternalLink className="w-3.5 h-3.5" /> Job Posting URL
                  </span>
                  <a
                    href={selectedApp.job_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-soft-blue underline font-semibold truncate block"
                  >
                    {selectedApp.job_url}
                  </a>
                </div>
              )}

              {selectedApp.tailored_resume_title && (
                <div className="well p-3 rounded-xl space-y-1 sm:col-span-2">
                  <span className="text-soft-muted font-medium flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-soft-blue" /> Attached Tailored Resume
                  </span>
                  <p className="font-bold text-soft-text">{selectedApp.tailored_resume_title}</p>
                </div>
              )}

              {selectedApp.notes && (
                <div className="well p-3 rounded-xl space-y-1 sm:col-span-2">
                  <span className="text-soft-muted font-medium">Application Notes</span>
                  <p className="text-soft-text leading-relaxed whitespace-pre-wrap">{selectedApp.notes}</p>
                </div>
              )}
            </div>

            {/* Activity History Timeline */}
            <div className="space-y-3 pt-2">
              <div className="text-xs font-bold uppercase tracking-wider text-soft-muted flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>Activity & Stage Timeline ({selectedApp.activities?.length || 0})</span>
              </div>

              <div className="space-y-2 border-l-2 border-slate-200 ml-2 pl-4">
                {selectedApp.activities?.map((act) => (
                  <div key={act.id} className="text-xs space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-soft-text uppercase text-[10px] well px-1.5 py-0.2 rounded">
                        {act.activity_type.replace("_", " ")}
                      </span>
                      <span className="text-[10px] text-soft-muted">
                        {new Date(act.created_at).toLocaleString()}
                      </span>
                    </div>
                    {act.note && <p className="text-soft-text font-medium">{act.note}</p>}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Opportunity Comparison Modal */}
      {showComparisonModal && comparisonResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="surface p-6 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto space-y-6 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b pb-4 border-slate-200">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg well text-indigo-600">
                  <Scale className="w-5 h-5 text-indigo-600" />
                </span>
                <h3 className="text-lg font-bold text-soft-text">
                  Side-by-Side Opportunity Comparison
                </h3>
              </div>
              <button
                onClick={() => setShowComparisonModal(false)}
                className="text-soft-muted hover:text-soft-text font-bold text-sm"
              >
                ✕
              </button>
            </div>

            {/* Comparative Summary Well */}
            <div className="well p-4 rounded-xl border-l-4 border-indigo-600 space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-800 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> Strategic Candidate Advantage
              </span>
              <p className="text-xs text-soft-text leading-relaxed font-medium">
                {comparisonResult.comparison_summary}
              </p>
            </div>

            {/* Comparison Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {comparisonResult.opportunities.map((opp) => (
                <div key={opp.application_id} className="surface p-4 rounded-xl space-y-4 border">
                  <div>
                    <span className="text-xs font-semibold text-soft-muted uppercase">
                      {opp.company_name}
                    </span>
                    <h4 className="text-base font-bold text-soft-text">{opp.job_title}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md well text-soft-blue">
                        {opp.stage}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getPriorityBadge(
                          opp.priority
                        )}`}
                      >
                        {opp.priority}
                      </span>
                    </div>
                  </div>

                  {/* Quantitative Match Gauge */}
                  <div className="well p-3 rounded-lg text-center space-y-1">
                    <div className="text-[10px] text-soft-muted font-bold uppercase">
                      Overall Match Score
                    </div>
                    <div className="text-2xl font-black text-soft-blue">
                      {typeof opp.overall_match_score === "number"
                        ? `${Math.round(opp.overall_match_score)}%`
                        : "N/A"}
                    </div>
                    <div className="grid grid-cols-2 gap-1 text-[10px] text-soft-muted pt-1 border-t border-slate-200">
                      <div>Skills: {opp.skill_match_score ? `${Math.round(opp.skill_match_score)}%` : "—"}</div>
                      <div>Exp: {opp.experience_score ? `${Math.round(opp.experience_score)}%` : "—"}</div>
                    </div>
                  </div>

                  {/* Top Demonstrated Skills */}
                  {opp.top_demonstrated_skills?.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-soft-green-text block">
                        Demonstrated Strengths
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {opp.top_demonstrated_skills.map((s, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Critical Missing Skills */}
                  {opp.critical_missing_skills?.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-soft-orange-text block">
                        Critical Gaps
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {opp.critical_missing_skills.map((s, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-orange-50 text-orange-800"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* New Application Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="surface p-6 rounded-2xl max-w-lg w-full space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b pb-3 border-slate-200">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-lg well text-soft-blue">
                  <Kanban className="w-5 h-5 text-soft-blue" />
                </span>
                <h3 className="text-lg font-bold text-soft-text">Track New Job Application</h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-soft-muted hover:text-soft-text font-bold text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              {/* Optional JD Link */}
              {jobs.length > 0 && (
                <div className="space-y-1.5">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Pre-fill from Analyzed Job Description (Optional)
                  </label>
                  <select
                    onChange={(e) => handleSelectJD(e.target.value)}
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  >
                    <option value="">— Select an analyzed job description —</option>
                    {jobs.map((j) => (
                      <option key={j.id} value={j.id}>
                        {j.job_title} at {j.company_name || "Company"}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={newAppForm.company_name}
                    onChange={(e) => setNewAppForm({ ...newAppForm, company_name: e.target.value })}
                    placeholder="e.g. Stripe, Google"
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    required
                    value={newAppForm.job_title}
                    onChange={(e) => setNewAppForm({ ...newAppForm, job_title: e.target.value })}
                    placeholder="e.g. Senior Backend Engineer"
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Initial Stage
                  </label>
                  <select
                    value={newAppForm.stage}
                    onChange={(e) => setNewAppForm({ ...newAppForm, stage: e.target.value })}
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  >
                    {STAGES.map((s) => (
                      <option key={s.key} value={s.key}>
                        {s.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Priority
                  </label>
                  <select
                    value={newAppForm.priority}
                    onChange={(e) => setNewAppForm({ ...newAppForm, priority: e.target.value })}
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  >
                    <option value="HIGH">High Priority</option>
                    <option value="MEDIUM">Medium Priority</option>
                    <option value="LOW">Low Priority</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Location
                  </label>
                  <input
                    type="text"
                    value={newAppForm.location || ""}
                    onChange={(e) => setNewAppForm({ ...newAppForm, location: e.target.value })}
                    placeholder="e.g. Remote, New York"
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Salary Range
                  </label>
                  <input
                    type="text"
                    value={newAppForm.salary_range || ""}
                    onChange={(e) => setNewAppForm({ ...newAppForm, salary_range: e.target.value })}
                    placeholder="e.g. $180,000 - $220,000"
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  />
                </div>
              </div>

              {/* Attach Match Evaluation */}
              {matches.length > 0 && (
                <div className="space-y-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Link Match Report (Optional)
                  </label>
                  <select
                    value={newAppForm.match_evaluation_id || ""}
                    onChange={(e) =>
                      setNewAppForm({
                        ...newAppForm,
                        match_evaluation_id: e.target.value || undefined,
                      })
                    }
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  >
                    <option value="">— None —</option>
                    {matches.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.job_title} ({Math.round(m.overall_score)}% Match)
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Attach Tailored Resume */}
              {tailoredResumes.length > 0 && (
                <div className="space-y-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-soft-muted">
                    Link Tailored Resume (Optional)
                  </label>
                  <select
                    value={newAppForm.tailored_resume_id || ""}
                    onChange={(e) =>
                      setNewAppForm({
                        ...newAppForm,
                        tailored_resume_id: e.target.value || undefined,
                      })
                    }
                    className="w-full text-xs rounded-xl border border-slate-200 well p-2.5 focus:outline-hidden focus:border-soft-blue font-medium"
                  >
                    <option value="">— None —</option>
                    {tailoredResumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.version_title}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-soft text-xs py-2 px-4"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="btn-primary text-xs py-2 px-4 flex items-center gap-2"
                >
                  {creating ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Saving Application...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      <span>Track Application</span>
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

export default function PipelinePage() {
  return (
    <Suspense
      fallback={
        <div className="surface p-12 text-center text-xs text-soft-muted rounded-2xl">
          Loading application tracker...
        </div>
      }
    >
      <PipelineContent />
    </Suspense>
  );
}
