"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Sparkles,
  Download,
  CheckCircle,
  XCircle,
  Edit3,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Building,
  RefreshCw,
  Plus,
  Trash2,
  Check,
  Eye,
  FileCheck,
} from "lucide-react";
import {
  deleteTailoredResume,
  exportDOCX,
  exportPDF,
  getTailoredResume,
  listJobs,
  listTailoredResumes,
  listUserResumes,
  tailorResume,
  updateDiff,
  JobDescriptionSummary,
  ResumeListItem,
  TailoredBulletDiff,
  TailoredResume,
  TailoredResumeSummary,
} from "@/lib/api";

function OptimizerContent() {
  const searchParams = useSearchParams();
  const queryJdId = searchParams.get("jd_id");
  const queryResumeId = searchParams.get("resume_id");

  const [drafts, setDrafts] = useState<TailoredResumeSummary[]>([]);
  const [selectedResume, setSelectedResume] = useState<TailoredResume | null>(null);
  const [loading, setLoading] = useState(true);
  const [tailoring, setTailoring] = useState(false);
  const [downloading, setDownloading] = useState<"pdf" | "docx" | null>(null);
  const [error, setError] = useState<string | null>(null);

  // New Tailoring Modal
  const [showModal, setShowModal] = useState(false);
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [jobs, setJobs] = useState<JobDescriptionSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [selectedJdId, setSelectedJdId] = useState("");

  // Inline editing state for a diff
  const [editingDiffId, setEditingDiffId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  useEffect(() => {
    loadDrafts(queryJdId, queryResumeId);
  }, [queryJdId, queryResumeId]);

  async function loadDrafts(targetJdId?: string | null, targetResumeId?: string | null) {
    try {
      setLoading(true);
      const data = await listTailoredResumes();
      setDrafts(data);

      if (targetJdId) {
        const found = data.find((d) => d.target_jd_id === targetJdId);
        if (found) {
          const first = await getTailoredResume(found.id);
          setSelectedResume(first);
          return;
        } else {
          openNewModal(targetJdId, targetResumeId);
          return;
        }
      }

      if (data.length > 0 && !selectedResume) {
        const first = await getTailoredResume(data[0].id);
        setSelectedResume(first);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load tailored resumes");
    } finally {
      setLoading(false);
    }
  }

  async function openNewModal(preselectJdId?: string | null, preselectResumeId?: string | null) {
    try {
      setError(null);
      const [resList, jobList] = await Promise.all([listUserResumes(), listJobs()]);
      setResumes(resList);
      setJobs(jobList);
      if (preselectResumeId && resList.some((r) => r.id === preselectResumeId)) {
        setSelectedResumeId(preselectResumeId);
      } else if (resList.length > 0) {
        setSelectedResumeId(resList[0].id);
      }

      if (preselectJdId && jobList.some((j) => j.id === preselectJdId)) {
        setSelectedJdId(preselectJdId);
      } else if (jobList.length > 0) {
        setSelectedJdId(jobList[0].id);
      }
      setShowModal(true);
    } catch (err: any) {
      setError(err.message || "Failed to load options");
    }
  }

  async function handleTailorSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedResumeId || !selectedJdId) {
      setError("Please select both a resume and target job.");
      return;
    }

    try {
      setTailoring(true);
      setError(null);
      const tailored = await tailorResume({
        resume_id: selectedResumeId,
        jd_id: selectedJdId,
      });

      setSelectedResume(tailored);
      setShowModal(false);
      await loadDrafts();
    } catch (err: any) {
      setError(err.message || "Failed to tailor resume");
    } finally {
      setTailoring(false);
    }
  }

  async function handleSelectDraft(id: string) {
    try {
      setError(null);
      const detail = await getTailoredResume(id);
      setSelectedResume(detail);
      setEditingDiffId(null);
    } catch (err: any) {
      setError(err.message || "Failed to load tailored draft");
    }
  }

  async function handleDiffAction(diff: TailoredBulletDiff, action: "ACCEPTED" | "REJECTED") {
    if (!selectedResume) return;
    try {
      const updatedDiff = await updateDiff(diff.id, { status: action });
      // Reload full snapshot to update live preview in real time
      const refreshed = await getTailoredResume(selectedResume.id);
      setSelectedResume(refreshed);
    } catch (err: any) {
      setError(err.message || "Failed to update diff");
    }
  }

  async function handleSaveCustomEdit(diffId: string) {
    if (!selectedResume || !editText.trim()) return;
    try {
      await updateDiff(diffId, { status: "EDITED", edited_text: editText.trim() });
      const refreshed = await getTailoredResume(selectedResume.id);
      setSelectedResume(refreshed);
      setEditingDiffId(null);
      setEditText("");
    } catch (err: any) {
      setError(err.message || "Failed to save edited bullet");
    }
  }

  async function handleExport(type: "pdf" | "docx") {
    if (!selectedResume) return;
    try {
      setDownloading(type);
      const blob = type === "pdf" ? await exportPDF(selectedResume.id) : await exportDOCX(selectedResume.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Tailored_Resume_${selectedResume.id}.${type}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || `Failed to export ${type.toUpperCase()}`);
    } finally {
      setDownloading(null);
    }
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this tailored resume version?")) return;
    try {
      await deleteTailoredResume(id);
      if (selectedResume?.id === id) {
        setSelectedResume(null);
      }
      await loadDrafts();
    } catch (err: any) {
      setError(err.message || "Failed to delete tailored resume");
    }
  }

  const diffs = selectedResume?.diffs || [];
  const acceptedCount = diffs.filter((d) => d.status === "ACCEPTED" || d.status === "EDITED").length;
  const pendingCount = diffs.filter((d) => d.status === "PENDING").length;

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-soft-text flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-soft-blue" />
            AI Resume Optimizer & Live Editor
          </h1>
          <p className="text-sm text-soft-muted mt-1">
            Role-targeted Google XYZ formula bullet rewriting bounded by strict NLI anti-hallucination verification.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => openNewModal()}
            className="btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            Tailor for Role
          </button>
          {selectedResume && (
            <>
              <button
                onClick={() => handleExport("pdf")}
                disabled={downloading !== null}
                className="btn-soft px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <Download className="w-4 h-4 text-soft-blue" />
                {downloading === "pdf" ? "Exporting PDF..." : "Export PDF"}
              </button>
              <button
                onClick={() => handleExport("docx")}
                disabled={downloading !== null}
                className="btn-soft px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <FileText className="w-4 h-4 text-soft-blue" />
                {downloading === "docx" ? "Exporting DOCX..." : "Export DOCX"}
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="font-semibold text-xs underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Split-Screen Workspace: Left = Diff Cards, Right = Live ATS Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (6 cols): Diff Approval Hub */}
        <div className="lg:col-span-6 space-y-5">
          {/* Version Selector Bar */}
          <div className="surface p-4 rounded-2xl flex items-center justify-between gap-3">
            <div className="truncate">
              <span className="text-[10px] font-bold uppercase text-soft-muted">
                Active Tailored Version
              </span>
              <p className="text-xs font-bold text-soft-text truncate">
                {selectedResume?.version_title || "No version selected"}
              </p>
            </div>

            {drafts.length > 1 && (
              <select
                value={selectedResume?.id || ""}
                onChange={(e) => handleSelectDraft(e.target.value)}
                className="text-xs rounded-xl well border border-white/60 p-2 text-soft-text focus:outline-none"
              >
                {drafts.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.job_title || d.version_title}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Diff Stats Banner */}
          {selectedResume && (
            <div className="grid grid-cols-3 gap-3">
              <div className="surface p-3 rounded-xl text-center">
                <span className="text-[10px] font-bold uppercase text-soft-muted">Total Diffs</span>
                <p className="text-base font-bold text-soft-text">{diffs.length}</p>
              </div>
              <div className="surface p-3 rounded-xl text-center">
                <span className="text-[10px] font-bold uppercase text-soft-muted">Applied</span>
                <p className="text-base font-bold text-soft-green-text">{acceptedCount}</p>
              </div>
              <div className="surface p-3 rounded-xl text-center">
                <span className="text-[10px] font-bold uppercase text-soft-muted">Pending Review</span>
                <p className="text-base font-bold text-soft-blue">{pendingCount}</p>
              </div>
            </div>
          )}

          {/* Diffs List */}
          {loading ? (
            <div className="surface p-12 text-center text-xs text-soft-muted rounded-2xl">
              Loading tailored diffs...
            </div>
          ) : !selectedResume || diffs.length === 0 ? (
            <div className="surface p-12 text-center rounded-2xl space-y-3">
              <FileCheck className="w-10 h-10 text-slate-300 mx-auto" />
              <h3 className="text-sm font-bold text-soft-text">No Tailored Diffs Available</h3>
              <p className="text-xs text-soft-muted max-w-sm mx-auto">
                Click &ldquo;Tailor for Role&rdquo; above to generate Google XYZ formula rewrites protected by NLI guardrails.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {diffs.map((diff, idx) => {
                const isAccepted = diff.status === "ACCEPTED";
                const isRejected = diff.status === "REJECTED";
                const isEdited = diff.status === "EDITED";
                const isEditingThis = editingDiffId === diff.id;

                return (
                  <div
                    key={diff.id}
                    className={`surface p-5 rounded-2xl space-y-3 border transition-all ${
                      isAccepted
                        ? "border-emerald-200 bg-emerald-50/20"
                        : isRejected
                        ? "border-slate-200 opacity-60"
                        : "border-white/80"
                    }`}
                  >
                    {/* Diff Header */}
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-soft-text">
                        Bullet #{idx + 1}
                      </span>

                      <div className="flex items-center gap-2">
                        {/* NLI Verification Tag */}
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 ${
                            diff.nli_verification_status === "ENTAILMENT"
                              ? "bg-emerald-50 text-soft-green-text border border-emerald-200"
                              : diff.nli_verification_status === "NEUTRAL"
                              ? "bg-amber-50 text-soft-orange-text border border-amber-200"
                              : "bg-red-50 text-red-700 border border-red-200"
                          }`}
                        >
                          <ShieldCheck className="w-3 h-3" />
                          {diff.nli_verification_status === "ENTAILMENT"
                            ? "Factual Entailment"
                            : diff.nli_verification_status}
                        </span>

                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                            isAccepted
                              ? "bg-emerald-100 text-emerald-800"
                              : isRejected
                              ? "bg-slate-200 text-slate-700"
                              : isEdited
                              ? "bg-blue-100 text-soft-blue"
                              : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {diff.status}
                        </span>
                      </div>
                    </div>

                    {/* Original Bullet */}
                    <div className="well p-3 rounded-xl text-xs text-soft-muted space-y-1 border border-white/60">
                      <p className="text-[10px] font-bold uppercase text-slate-400">Original Bullet</p>
                      <p className="line-through text-slate-500 leading-relaxed">
                        {diff.original_text}
                      </p>
                    </div>

                    {/* Optimized or Edited Bullet */}
                    <div className="surface p-3.5 rounded-xl text-xs text-soft-text space-y-1 border border-blue-200/60 bg-blue-50/20">
                      <p className="text-[10px] font-bold uppercase text-soft-blue flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        {isEdited ? "Customized Version" : "Google XYZ Optimization"}
                      </p>
                      {isEditingThis ? (
                        <div className="space-y-2 pt-1">
                          <textarea
                            rows={3}
                            value={editText}
                            onChange={(e) => setEditText(e.target.value)}
                            className="w-full text-xs rounded-xl well border border-white/80 p-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue resize-none"
                          />
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => setEditingDiffId(null)}
                              className="text-xs px-3 py-1 rounded-lg btn-soft cursor-pointer"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => handleSaveCustomEdit(diff.id)}
                              className="text-xs px-3 py-1 rounded-lg btn-primary cursor-pointer"
                            >
                              Save Bullet
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="font-medium text-slate-800 leading-relaxed">
                          {isEdited && diff.edited_text ? diff.edited_text : diff.optimized_text}
                        </p>
                      )}
                    </div>

                    {/* Rationale */}
                    <p className="text-[11px] text-soft-muted italic">
                      Rationale: {diff.rationale}
                    </p>

                    {/* Actions */}
                    {!isEditingThis && (
                      <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-200/50">
                        <button
                          onClick={() => {
                            setEditingDiffId(diff.id);
                            setEditText(diff.edited_text || diff.optimized_text);
                          }}
                          className="btn-soft px-3 py-1.5 rounded-xl text-xs font-semibold text-soft-muted hover:text-soft-text flex items-center gap-1 cursor-pointer"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          Edit
                        </button>
                        <button
                          onClick={() => handleDiffAction(diff, "REJECTED")}
                          className={`btn-soft px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1 cursor-pointer ${
                            isRejected ? "bg-slate-300 font-bold" : "text-slate-500 hover:text-red-600"
                          }`}
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          Reject
                        </button>
                        <button
                          onClick={() => handleDiffAction(diff, "ACCEPTED")}
                          className={`btn-primary px-4 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1 cursor-pointer ${
                            isAccepted ? "bg-emerald-600" : ""
                          }`}
                        >
                          <Check className="w-3.5 h-3.5" />
                          {isAccepted ? "Applied" : "Accept Rewrite"}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column (6 cols): Live ATS Document Preview Canvas */}
        <div className="lg:col-span-6 sticky top-6">
          <div className="surface p-6 rounded-2xl space-y-4 border border-white/80">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/50">
              <span className="text-xs font-bold text-soft-text flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-soft-blue" />
                Live ATS Single-Column Preview
              </span>
              <span className="text-[10px] uppercase font-bold text-soft-muted bg-slate-100 px-2 py-0.5 rounded">
                Real-Time Render
              </span>
            </div>

            {/* A4 Document Simulation Canvas */}
            <div className="bg-white rounded-xl p-8 shadow-inner border border-slate-200 min-h-[580px] max-h-[720px] overflow-y-auto space-y-5 text-slate-800 font-sans text-xs">
              {/* Candidate Header */}
              <div className="text-center space-y-1 pb-3 border-b border-slate-200">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight uppercase">
                  {selectedResume?.tailored_content?.candidate_name || "Marcus Vance"}
                </h2>
                <p className="text-[10px] text-slate-500">
                  {selectedResume?.tailored_content?.contact_info || "marcus@example.com | San Francisco, CA"}
                </p>
              </div>

              {/* Sections Rendered */}
              {(selectedResume?.tailored_content?.sections || []).map((sec: any, sIdx: number) => (
                <div key={sec.id || sIdx} className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-soft-blue border-b border-slate-100 pb-0.5">
                    {sec.heading || sec.section_type}
                  </h3>

                  {/* Items */}
                  {sec.items?.map((item: any, iIdx: number) => (
                    <div key={item.id || iIdx} className="space-y-1">
                      <div className="flex justify-between items-baseline">
                        <span className="font-bold text-slate-900">{item.title}</span>
                        {item.start_date && (
                          <span className="text-[10px] text-slate-400">
                            {item.start_date} - {item.end_date || "Present"}
                          </span>
                        )}
                      </div>

                      {item.organization && (
                        <p className="text-[10px] italic text-slate-500">
                          {item.organization} {item.location ? `| ${item.location}` : ""}
                        </p>
                      )}

                      <ul className="list-disc list-outside pl-4 space-y-1 pt-0.5">
                        {item.bullets?.map((b: string, bIdx: number) => (
                          <li key={bIdx} className="text-[11px] leading-relaxed text-slate-700">
                            {b}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}

                  {/* Raw content block (e.g. skills) */}
                  {!sec.items?.length && sec.raw_content && (
                    <p className="text-[11px] leading-relaxed text-slate-700">
                      {sec.raw_content}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* New Tailoring Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="surface p-6 rounded-2xl max-w-lg w-full space-y-5 border border-white/80 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-soft-text flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-soft-blue" />
                Tailor Resume for Job Opportunity
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleTailorSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Source Resume *
                </label>
                {resumes.length === 0 ? (
                  <p className="text-xs text-red-600 well p-3 rounded-xl">
                    No resumes uploaded. Please upload a resume first.
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
                  Target Job Description *
                </label>
                {jobs.length === 0 ? (
                  <p className="text-xs text-red-600 well p-3 rounded-xl">
                    No jobs analyzed. Please analyze a job in JD Intelligence first.
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
                        {j.job_title} ({j.company_name || "Company"})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="btn-soft px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={tailoring || resumes.length === 0 || jobs.length === 0}
                  className="btn-primary px-5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {tailoring ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Generating NLI-Verified Diffs...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Generate Tailored Diffs
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

export default function OptimizerPage() {
  return (
    <Suspense
      fallback={
        <div className="surface p-12 text-center text-xs text-soft-muted rounded-2xl">
          Loading AI Resume Studio...
        </div>
      }
    >
      <OptimizerContent />
    </Suspense>
  );
}
