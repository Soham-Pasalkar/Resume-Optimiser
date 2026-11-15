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
  RotateCcw,
  Layers,
  Target,
  Sliders,
  ChevronRight,
  Info,
  ListFilter,
  CheckSquare,
  Square,
  Award,
  BookOpen,
  HelpCircle,
} from "lucide-react";
import {
  deleteTailoredResume,
  exportDOCX,
  exportPDF,
  getTailoredResume,
  getATSAnalysis,
  addCustomEvidence,
  listJobs,
  listTailoredResumes,
  listUserResumes,
  restoreDiff,
  tailorResume,
  toggleSectionVisibility,
  updateDiff,
  ATSAnalysis,
  JobDescriptionSummary,
  MissingRequirementItem,
  RequirementEvidenceMapping,
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
  const [atsAnalysis, setAtsAnalysis] = useState<ATSAnalysis | null>(null);
  const [loadingAts, setLoadingAts] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [tailoring, setTailoring] = useState(false);
  const [downloading, setDownloading] = useState<"pdf" | "docx" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"review" | "mappings" | "sections" | "ats">("review");
  const [tierFilter, setTierFilter] = useState<"ALL" | "DEMONSTRATED" | "TRANSFERABLE" | "PROFILE_LISTED" | "MISSING">("ALL");

  // New Tailoring Modal
  const [showModal, setShowModal] = useState(false);
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [jobs, setJobs] = useState<JobDescriptionSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [selectedJdId, setSelectedJdId] = useState("");

  // Custom Evidence Modal
  const [evidenceModalReq, setEvidenceModalReq] = useState<RequirementEvidenceMapping | MissingRequirementItem | null>(null);
  const [customEvidenceText, setCustomEvidenceText] = useState("");
  const [customEvidenceUrl, setCustomEvidenceUrl] = useState("");
  const [submittingEvidence, setSubmittingEvidence] = useState(false);

  // Inline editing state for a diff
  const [editingDiffId, setEditingDiffId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");

  // Section toggle state
  const [togglingSecId, setTogglingSecId] = useState<string | null>(null);

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
          loadAtsData(first.id, first.tailored_content?.ats_analysis);
          return;
        } else {
          openNewModal(targetJdId, targetResumeId);
          return;
        }
      }

      if (data.length > 0 && !selectedResume) {
        const first = await getTailoredResume(data[0].id);
        setSelectedResume(first);
        loadAtsData(first.id, first.tailored_content?.ats_analysis);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load tailored resumes");
    } finally {
      setLoading(false);
    }
  }

  async function loadAtsData(tailoredId: string, preloaded?: any) {
    if (preloaded && preloaded.job_compatibility && preloaded.ats_readability) {
      setAtsAnalysis(preloaded);
    }
    try {
      setLoadingAts(true);
      const data = await getATSAnalysis(tailoredId);
      setAtsAnalysis(data);
    } catch (err) {
      console.warn("Could not load fresh ATS analysis:", err);
    } finally {
      setLoadingAts(false);
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
      const created = await tailorResume({
        resume_id: selectedResumeId,
        jd_id: selectedJdId,
      });
      setShowModal(false);
      setSelectedResume(created);
      setDrafts((prev) => [
        {
          id: created.id,
          user_id: created.user_id,
          source_resume_id: created.source_resume_id,
          target_jd_id: created.target_jd_id,
          version_title: created.version_title,
          job_title: created.job_title,
          company_name: created.company_name,
          diffs_count: created.diffs_count,
          created_at: created.created_at,
        },
        ...prev,
      ]);
      loadAtsData(created.id, created.tailored_content?.ats_analysis);
    } catch (err: any) {
      setError(err.message || "Tailoring failed.");
    } finally {
      setTailoring(false);
    }
  }

  async function handleSelectResume(id: string) {
    try {
      setLoading(true);
      const detail = await getTailoredResume(id);
      setSelectedResume(detail);
      loadAtsData(detail.id, detail.tailored_content?.ats_analysis);
    } catch (err: any) {
      setError(err.message || "Failed to load draft detail.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDiffAction(diff: TailoredBulletDiff, newStatus: string, customText?: string) {
    if (!selectedResume) return;
    try {
      const updatedDiff = await updateDiff(diff.id, {
        status: newStatus,
        edited_text: customText,
      });

      // Update local diffs
      const newDiffs = selectedResume.diffs.map((d) =>
        d.id === diff.id ? updatedDiff : d
      );

      // Re-fetch tailored resume to get synchronized IR snapshot
      const refreshed = await getTailoredResume(selectedResume.id);
      setSelectedResume({
        ...refreshed,
        diffs: newDiffs,
      });
      loadAtsData(refreshed.id, refreshed.tailored_content?.ats_analysis);
      setEditingDiffId(null);
    } catch (err: any) {
      setError(err.message || "Failed to update bullet diff.");
    }
  }

  async function handleRestoreOriginal(diffId: string) {
    if (!selectedResume) return;
    try {
      const restored = await restoreDiff(diffId);
      const newDiffs = selectedResume.diffs.map((d) =>
        d.id === diffId ? restored : d
      );
      const refreshed = await getTailoredResume(selectedResume.id);
      setSelectedResume({
        ...refreshed,
        diffs: newDiffs,
      });
      loadAtsData(refreshed.id, refreshed.tailored_content?.ats_analysis);
    } catch (err: any) {
      setError(err.message || "Failed to restore bullet to original.");
    }
  }

  async function handleSaveCustomEdit(diffId: string) {
    const diff = selectedResume?.diffs.find((d) => d.id === diffId);
    if (!diff) return;
    await handleDiffAction(diff, "EDITED", editText);
  }

  async function handleToggleSection(secId: string, currentIncluded: boolean) {
    if (!selectedResume) return;
    try {
      setTogglingSecId(secId);
      const updated = await toggleSectionVisibility(selectedResume.id, secId, !currentIncluded);
      setSelectedResume(updated);
      loadAtsData(updated.id, updated.tailored_content?.ats_analysis);
    } catch (err: any) {
      setError(err.message || "Failed to toggle section.");
    } finally {
      setTogglingSecId(null);
    }
  }

  async function handleAddCustomEvidenceSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedResume || !evidenceModalReq || !customEvidenceText.trim()) return;

    try {
      setSubmittingEvidence(true);
      const reqId = "requirement_id" in evidenceModalReq ? evidenceModalReq.requirement_id : (evidenceModalReq as any).id;
      const updated = await addCustomEvidence(selectedResume.id, {
        requirement_id: reqId,
        evidence_text: customEvidenceText.trim(),
        section_name: "Candidate Self-Attestation",
        evidence_url: customEvidenceUrl.trim() || undefined,
      });
      setSelectedResume(updated);
      setEvidenceModalReq(null);
      setCustomEvidenceText("");
      setCustomEvidenceUrl("");
      loadAtsData(selectedResume.id);
    } catch (err: any) {
      setError(err.message || "Failed to attach custom evidence.");
    } finally {
      setSubmittingEvidence(false);
    }
  }

  async function handleExport(format: "pdf" | "docx") {
    if (!selectedResume) return;
    try {
      setDownloading(format);
      const blob = format === "pdf" ? await exportPDF(selectedResume.id) : await exportDOCX(selectedResume.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selectedResume.version_title.replace(/\s+/g, "_")}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setError(err.message || `Failed to export ${format.toUpperCase()}`);
    } finally {
      setDownloading(null);
    }
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this tailored resume draft?")) return;
    try {
      await deleteTailoredResume(id);
      setDrafts((prev) => prev.filter((d) => d.id !== id));
      if (selectedResume?.id === id) {
        setSelectedResume(null);
        setAtsAnalysis(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to delete version.");
    }
  }

  const diffs = selectedResume?.diffs || [];
  const acceptedCount = diffs.filter((d) => d.status === "ACCEPTED").length;
  const pendingCount = diffs.filter((d) => d.status === "PENDING").length;
  const verifiedCount = diffs.filter((d) => ["VERIFIED", "ENTAILMENT"].includes(d.nli_verification_status)).length;

  const content = selectedResume?.tailored_content || {};
  const rawSections = content.raw_sections || content.sections || [];
  const reqMappings: RequirementEvidenceMapping[] = content.requirement_mappings || [];
  const missingReqs: MissingRequirementItem[] = content.missing_requirements || [];

  // Combine into unified 4-tier list
  const combinedRequirements: RequirementEvidenceMapping[] = [
    ...reqMappings,
    ...missingReqs
      .filter((m) => !reqMappings.some((rm) => rm.requirement_id === m.requirement_id))
      .map((m) => ({
        requirement_id: m.requirement_id,
        requirement_text: m.requirement_text,
        is_mandatory: m.is_mandatory,
        canonical_skill_name: m.canonical_skill_name,
        category: m.category,
        matching_method: "UNMATCHED",
        confidence_score: 0.0,
        verification_status: "UNMATCHED",
        match_category: "MISSING",
        explanation: "No direct or transferable evidence found in candidate resume or profile.",
        requires_human_verification: true,
        suggested_action: m.suggested_action,
      })),
  ];

  const filteredRequirements = combinedRequirements.filter((req) => {
    if (tierFilter === "ALL") return true;
    const cat = req.match_category || "MISSING";
    return cat === tierFilter;
  });

  const demonstratedCount = combinedRequirements.filter((r) => r.match_category === "DEMONSTRATED").length;
  const transferableCount = combinedRequirements.filter((r) => r.match_category === "TRANSFERABLE").length;
  const profileListedCount = combinedRequirements.filter((r) => r.match_category === "PROFILE_LISTED").length;
  const missingCount = combinedRequirements.filter((r) => (r.match_category || "MISSING") === "MISSING").length;

  const compScore = atsAnalysis?.job_compatibility?.score ?? 0;
  const readScore = atsAnalysis?.ats_readability?.score ?? 0;

  return (
    <div className="space-y-6 pb-20">
      {/* Header Hub */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-soft-text flex items-center gap-2.5">
            <Sparkles className="w-6 h-6 text-soft-blue" />
            Resume Studio 2.0
          </h1>
          <p className="text-xs sm:text-sm text-soft-muted mt-1">
            Job-targeted, ATS-engineered resume optimization strictly preserving factual career evidence.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => openNewModal()}
            className="btn-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 cursor-pointer shadow-sm hover:opacity-95"
          >
            <Plus className="w-4 h-4" />
            Tailor for Role
          </button>

          {selectedResume && (
            <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl">
              <button
                onClick={() => handleExport("pdf")}
                disabled={downloading !== null}
                className="btn-soft px-3 py-1.5 rounded-lg text-xs font-semibold text-soft-text flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                title="Download ATS Single-Column PDF"
              >
                {downloading === "pdf" ? (
                  <div className="w-3.5 h-3.5 border-2 border-slate-700 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5 text-red-600" />
                )}
                PDF
              </button>
              <button
                onClick={() => handleExport("docx")}
                disabled={downloading !== null}
                className="btn-soft px-3 py-1.5 rounded-lg text-xs font-semibold text-soft-text flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                title="Download ATS Word DOCX"
              >
                {downloading === "docx" ? (
                  <div className="w-3.5 h-3.5 border-2 border-slate-700 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <FileText className="w-3.5 h-3.5 text-blue-600" />
                )}
                Word
              </button>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="surface p-4 rounded-xl border border-red-200 bg-red-50 text-red-700 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 font-bold ml-2">
            ✕
          </button>
        </div>
      )}

      {/* Target Role Context Banner & Transparent Dual ATS Scorecards */}
      {selectedResume && (
        <div className="space-y-4">
          {/* Target Role Context Banner */}
          <div className="surface p-4 rounded-2xl border border-white/80 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xs">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-soft-blue px-2 py-0.5 rounded-md">
                  Active Target Opportunity
                </span>
                <span className="text-xs font-bold text-soft-text">
                  {selectedResume.job_title || "Target Role"}
                </span>
                {selectedResume.company_name && (
                  <span className="text-xs text-soft-muted flex items-center gap-1">
                    <Building className="w-3 h-3 text-slate-400" />
                    {selectedResume.company_name}
                  </span>
                )}
              </div>
              <p className="text-xs text-soft-muted font-medium">
                {selectedResume.version_title} • Draft ID: {selectedResume.id.slice(0, 8)}
              </p>
            </div>

            <div className="flex items-center gap-2">
              {drafts.length > 1 && (
                <select
                  value={selectedResume.id}
                  onChange={(e) => handleSelectResume(e.target.value)}
                  className="text-xs rounded-xl well border border-white/60 p-2 text-soft-text focus:outline-none"
                >
                  {drafts.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.job_title || d.version_title}
                    </option>
                  ))}
                </select>
              )}
              <button
                onClick={(e) => handleDelete(selectedResume.id, e)}
                className="p-2 text-slate-400 hover:text-red-600 rounded-lg btn-soft cursor-pointer"
                title="Delete version"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Transparent Dual ATS Scorecards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            {/* Scorecard 1: Job Compatibility Score */}
            <div className="md:col-span-6 surface p-4 rounded-2xl border border-white/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    compScore >= 75 ? "bg-emerald-100 text-emerald-800" : compScore >= 50 ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"
                  }`}>
                    {Math.round(compScore)}%
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-soft-text">Job Compatibility Score</h3>
                    <p className="text-[10px] text-soft-muted">Algorithmic role fit based on verified candidate evidence</p>
                  </div>
                </div>

                <button
                  onClick={() => setActiveTab("ats")}
                  className="text-[11px] font-bold text-soft-blue hover:underline cursor-pointer"
                >
                  View Audit →
                </button>
              </div>

              {/* Progress metric bars */}
              <div className="grid grid-cols-5 gap-1.5 text-center pt-1">
                <div className="well p-2 rounded-xl">
                  <span className="text-[9px] font-bold uppercase text-soft-muted block">Mandatory</span>
                  <span className="text-xs font-bold text-emerald-700">
                    {atsAnalysis?.job_compatibility?.breakdown?.mandatory_score ?? 0}/40
                  </span>
                </div>
                <div className="well p-2 rounded-xl">
                  <span className="text-[9px] font-bold uppercase text-soft-muted block">Preferred</span>
                  <span className="text-xs font-bold text-blue-700">
                    {atsAnalysis?.job_compatibility?.breakdown?.preferred_score ?? 0}/20
                  </span>
                </div>
                <div className="well p-2 rounded-xl">
                  <span className="text-[9px] font-bold uppercase text-soft-muted block">Transferable</span>
                  <span className="text-xs font-bold text-amber-700">
                    {atsAnalysis?.job_compatibility?.breakdown?.transferable_score ?? 0}/15
                  </span>
                </div>
                <div className="well p-2 rounded-xl">
                  <span className="text-[9px] font-bold uppercase text-soft-muted block">Profile</span>
                  <span className="text-xs font-bold text-purple-700">
                    {atsAnalysis?.job_compatibility?.breakdown?.profile_score ?? 0}/15
                  </span>
                </div>
                <div className="well p-2 rounded-xl">
                  <span className="text-[9px] font-bold uppercase text-soft-muted block">Depth</span>
                  <span className="text-xs font-bold text-slate-700">
                    {atsAnalysis?.job_compatibility?.breakdown?.depth_score ?? 0}/10
                  </span>
                </div>
              </div>
            </div>

            {/* Scorecard 2: ATS Readability Score */}
            <div className="md:col-span-6 surface p-4 rounded-2xl border border-white/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    readScore >= 80 ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                  }`}>
                    {Math.round(readScore)}%
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-soft-text">ATS Readability Score</h3>
                    <p className="text-[10px] text-soft-muted">Document parsing verified across enterprise standard parsers</p>
                  </div>
                </div>

                <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  ✓ Byte-Verified
                </span>
              </div>

              {/* Readability checkpoints */}
              <div className="grid grid-cols-3 gap-1.5 text-center pt-1">
                <div className="well p-2 rounded-xl">
                  <span className="text-[9px] font-bold uppercase text-soft-muted block">Standard Headings</span>
                  <span className="text-xs font-bold text-soft-text">
                    {atsAnalysis?.ats_readability?.breakdown?.standard_headings ?? 20}/20
                  </span>
                </div>
                <div className="well p-2 rounded-xl">
                  <span className="text-[9px] font-bold uppercase text-soft-muted block">Single-Column IR</span>
                  <span className="text-xs font-bold text-soft-text">
                    {atsAnalysis?.ats_readability?.breakdown?.document_structure ?? 15}/15
                  </span>
                </div>
                <div className="well p-2 rounded-xl">
                  <span className="text-[9px] font-bold uppercase text-soft-muted block">Byte Extraction</span>
                  <span className="text-xs font-bold text-emerald-700">
                    {atsAnalysis?.ats_readability?.breakdown?.text_extraction_validation ?? 20}/20
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Split-Screen Workspace: Left = Controls & Diffs, Right = Live ATS Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (6 cols): Review & Controls Hub */}
        <div className="lg:col-span-6 space-y-5">
          {/* Subsystem Navigation Tabs */}
          {selectedResume && (
            <div className="flex items-center gap-1.5 p-1.5 well rounded-2xl border border-white/60">
              <button
                onClick={() => setActiveTab("review")}
                className={`flex-1 py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 transition-all cursor-pointer ${
                  activeTab === "review" ? "btn-primary shadow-xs" : "text-soft-muted hover:text-soft-text"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Diffs ({diffs.length})
              </button>
              <button
                onClick={() => setActiveTab("mappings")}
                className={`flex-1 py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 transition-all cursor-pointer ${
                  activeTab === "mappings" ? "btn-primary shadow-xs" : "text-soft-muted hover:text-soft-text"
                }`}
              >
                <Target className="w-3.5 h-3.5" />
                Requirements ({combinedRequirements.length})
              </button>
              <button
                onClick={() => setActiveTab("sections")}
                className={`flex-1 py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 transition-all cursor-pointer ${
                  activeTab === "sections" ? "btn-primary shadow-xs" : "text-soft-muted hover:text-soft-text"
                }`}
              >
                <Sliders className="w-3.5 h-3.5" />
                Sections ({rawSections.length})
              </button>
              <button
                onClick={() => setActiveTab("ats")}
                className={`flex-1 py-2 px-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 transition-all cursor-pointer ${
                  activeTab === "ats" ? "btn-primary shadow-xs" : "text-soft-muted hover:text-soft-text"
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                ATS Audit
              </button>
            </div>
          )}

          {/* TAB 1: Bullet Diffs Review Hub */}
          {activeTab === "review" && (
            <div className="space-y-4">
              {loading ? (
                <div className="surface p-12 text-center text-xs text-soft-muted rounded-2xl">
                  Loading tailored diffs...
                </div>
              ) : !selectedResume || diffs.length === 0 ? (
                <div className="surface p-12 text-center rounded-2xl space-y-3">
                  <FileCheck className="w-10 h-10 text-slate-300 mx-auto" />
                  <h3 className="text-sm font-bold text-soft-text">No Tailored Diffs Available</h3>
                  <p className="text-xs text-soft-muted max-w-sm mx-auto">
                    Click &ldquo;Tailor for Role&rdquo; above to generate role-targeted rewrites protected by multi-layer factual guardrails.
                  </p>
                </div>
              ) : (
                diffs.map((diff, idx) => {
                  const isAccepted = diff.status === "ACCEPTED";
                  const isRejected = diff.status === "REJECTED";
                  const isEdited = diff.status === "EDITED";
                  const isEditingThis = editingDiffId === diff.id;
                  const isVerified = ["VERIFIED", "ENTAILMENT"].includes(diff.nli_verification_status);
                  const isFlagged = diff.nli_verification_status === "FLAGGED";

                  return (
                    <div
                      key={diff.id}
                      className="surface p-4 sm:p-5 rounded-2xl space-y-3.5 border border-white/80 transition-all hover:border-blue-200/50 shadow-xs"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[11px] font-bold text-soft-muted uppercase tracking-wider">
                          Bullet {idx + 1}
                        </span>

                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 ${
                              isVerified
                                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                                : isFlagged
                                ? "bg-red-50 text-red-800 border border-red-200"
                                : "bg-amber-50 text-amber-800 border border-amber-200"
                            }`}
                          >
                            {isVerified ? (
                              <ShieldCheck className="w-3 h-3 text-soft-green" />
                            ) : isFlagged ? (
                              <XCircle className="w-3 h-3 text-red-600" />
                            ) : (
                              <AlertTriangle className="w-3 h-3 text-amber-600" />
                            )}
                            {isVerified
                              ? "Factual Guardrail Verified"
                              : isFlagged
                              ? "Factual Drift Flagged"
                              : "Requires Semantic Review"}
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
                        <p className={`${isAccepted ? "line-through text-slate-400" : "text-slate-600"} leading-relaxed`}>
                          {diff.original_text}
                        </p>
                      </div>

                      {/* Optimized or Edited Bullet */}
                      <div className="surface p-3.5 rounded-xl text-xs text-soft-text space-y-1 border border-blue-200/60 bg-blue-50/20">
                        <p className="text-[10px] font-bold uppercase text-soft-blue flex items-center gap-1">
                          <Sparkles className="w-3 h-3" />
                          {isEdited ? "Customized Version" : "Tailored Active Presentation"}
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

                      {/* Candidate Actions */}
                      {!isEditingThis && (
                        <div className="flex items-center justify-between pt-2 border-t border-slate-200/50">
                          <div>
                            {(isAccepted || isEdited) && (
                              <button
                                onClick={() => handleRestoreOriginal(diff.id)}
                                className="text-[11px] font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1 cursor-pointer"
                                title="Revert to candidate's original wording"
                              >
                                <RotateCcw className="w-3 h-3" />
                                Restore Original
                              </button>
                            )}
                          </div>

                          <div className="flex items-center gap-2">
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
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* TAB 2: 4-Tier Requirement-to-Evidence Matrix */}
          {activeTab === "mappings" && (
            <div className="space-y-4">
              <div className="surface p-4 rounded-2xl border border-white/80 space-y-2">
                <h3 className="text-xs font-bold text-soft-text flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-purple-600" />
                  4-Tier Requirement-to-Evidence Matrix
                </h3>
                <p className="text-[11px] text-soft-muted">
                  Every job requirement classified into 4 transparent tiers: Demonstrated, Transferable, Profile Listed, or Missing.
                </p>

                {/* 4-Tier Filter Badges */}
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <button
                    onClick={() => setTierFilter("ALL")}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg cursor-pointer ${
                      tierFilter === "ALL" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    All ({combinedRequirements.length})
                  </button>
                  <button
                    onClick={() => setTierFilter("DEMONSTRATED")}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg cursor-pointer flex items-center gap-1 ${
                      tierFilter === "DEMONSTRATED"
                        ? "bg-emerald-700 text-white"
                        : "bg-emerald-50 text-emerald-800 border border-emerald-200 hover:bg-emerald-100"
                    }`}
                  >
                    <ShieldCheck className="w-3 h-3" />
                    Demonstrated ({demonstratedCount})
                  </button>
                  <button
                    onClick={() => setTierFilter("TRANSFERABLE")}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg cursor-pointer flex items-center gap-1 ${
                      tierFilter === "TRANSFERABLE"
                        ? "bg-blue-700 text-white"
                        : "bg-blue-50 text-blue-800 border border-blue-200 hover:bg-blue-100"
                    }`}
                  >
                    <Sliders className="w-3 h-3" />
                    Transferable ({transferableCount})
                  </button>
                  <button
                    onClick={() => setTierFilter("PROFILE_LISTED")}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg cursor-pointer flex items-center gap-1 ${
                      tierFilter === "PROFILE_LISTED"
                        ? "bg-purple-700 text-white"
                        : "bg-purple-50 text-purple-800 border border-purple-200 hover:bg-purple-100"
                    }`}
                  >
                    <Layers className="w-3 h-3" />
                    Profile Listed ({profileListedCount})
                  </button>
                  <button
                    onClick={() => setTierFilter("MISSING")}
                    className={`text-[10px] font-bold px-2.5 py-1 rounded-lg cursor-pointer flex items-center gap-1 ${
                      tierFilter === "MISSING"
                        ? "bg-rose-700 text-white"
                        : "bg-rose-50 text-rose-800 border border-rose-200 hover:bg-rose-100"
                    }`}
                  >
                    <AlertTriangle className="w-3 h-3" />
                    Missing ({missingCount})
                  </button>
                </div>
              </div>

              {/* Requirement Cards */}
              <div className="space-y-3">
                {filteredRequirements.length === 0 ? (
                  <div className="surface p-8 rounded-2xl text-xs text-soft-muted text-center">
                    No requirements found under this category filter.
                  </div>
                ) : (
                  filteredRequirements.map((req) => {
                    const cat = req.match_category || "MISSING";
                    const isDemonstrated = cat === "DEMONSTRATED";
                    const isTransferable = cat === "TRANSFERABLE";
                    const isProfileListed = cat === "PROFILE_LISTED";
                    const isMissing = cat === "MISSING";

                    return (
                      <div
                        key={req.requirement_id}
                        className={`surface p-4 rounded-2xl border space-y-2.5 ${
                          isDemonstrated
                            ? "border-emerald-200/80 bg-emerald-50/10"
                            : isTransferable
                            ? "border-blue-200/80 bg-blue-50/10"
                            : isProfileListed
                            ? "border-purple-200/80 bg-purple-50/10"
                            : "border-rose-200/80 bg-rose-50/10"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              {/* 4-Tier Badge */}
                              <span
                                className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded-full flex items-center gap-1 ${
                                  isDemonstrated
                                    ? "bg-emerald-100 text-emerald-800"
                                    : isTransferable
                                    ? "bg-blue-100 text-blue-800"
                                    : isProfileListed
                                    ? "bg-purple-100 text-purple-800"
                                    : "bg-rose-100 text-rose-800"
                                }`}
                              >
                                {isDemonstrated && <ShieldCheck className="w-3 h-3" />}
                                {isTransferable && <Sliders className="w-3 h-3" />}
                                {isProfileListed && <Layers className="w-3 h-3" />}
                                {isMissing && <AlertTriangle className="w-3 h-3" />}
                                {cat}
                              </span>

                              <span
                                className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                                  req.is_mandatory
                                    ? "bg-red-50 text-red-700 border border-red-200"
                                    : "bg-slate-100 text-slate-600 border border-slate-200"
                                }`}
                              >
                                {req.is_mandatory ? "Mandatory" : "Preferred"}
                              </span>

                              <span className="text-xs font-bold text-soft-text">
                                {req.canonical_skill_name || "Skill Requirement"}
                              </span>
                            </div>

                            <p className="text-xs text-slate-800 font-medium leading-snug">
                              {req.requirement_text}
                            </p>
                          </div>

                          <button
                            onClick={() => {
                              setEvidenceModalReq(req);
                              setCustomEvidenceText(req.original_evidence_text || "");
                              setCustomEvidenceUrl("");
                            }}
                            className="btn-soft px-2.5 py-1 rounded-lg text-[10px] font-bold text-soft-blue flex items-center gap-1 shrink-0 cursor-pointer"
                          >
                            <Plus className="w-3 h-3" />
                            {isMissing ? "Add Evidence" : "Update Evidence"}
                          </button>
                        </div>

                        {/* Explanation */}
                        {req.explanation && (
                          <p className="text-[11px] text-slate-600 italic">
                            {req.explanation}
                          </p>
                        )}

                        {/* Matched Evidence Snippet */}
                        {req.original_evidence_text && (
                          <div className="well p-2.5 rounded-xl text-[11px] text-slate-700 border border-white/60 space-y-1">
                            <span className="text-[9px] font-bold uppercase text-slate-400 flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              Evidence in {req.matched_section_name || "Candidate Profile"}
                            </span>
                            <p className="italic font-medium">&ldquo;{req.original_evidence_text}&rdquo;</p>
                          </div>
                        )}

                        {/* Suggested Action for Gaps */}
                        {req.suggested_action && isMissing && (
                          <p className="text-[10px] text-amber-700 font-medium">
                            Suggestion: {req.suggested_action}
                          </p>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Section Management Panel */}
          {activeTab === "sections" && (
            <div className="space-y-4">
              <div className="surface p-4 rounded-2xl border border-white/80 space-y-1">
                <h3 className="text-xs font-bold text-soft-text flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-soft-blue" />
                  Section Visibility & Hierarchy
                </h3>
                <p className="text-[11px] text-soft-muted">
                  Toggle sections to include or exclude from the final ATS document export.
                </p>
              </div>

              <div className="space-y-2.5">
                {rawSections.map((sec: any, idx: number) => {
                  const isIncluded = sec.is_included !== false;
                  const isToggling = togglingSecId === sec.id;

                  return (
                    <div
                      key={sec.id || idx}
                      className="surface p-4 rounded-2xl border border-white/80 flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => handleToggleSection(sec.id, isIncluded)}
                          disabled={isToggling}
                          className="cursor-pointer text-soft-blue disabled:opacity-50"
                        >
                          {isIncluded ? (
                            <CheckSquare className="w-5 h-5 text-emerald-600" />
                          ) : (
                            <Square className="w-5 h-5 text-slate-400" />
                          )}
                        </button>
                        <div>
                          <h4 className="text-xs font-bold text-soft-text uppercase tracking-wide">
                            {sec.heading || sec.section_type}
                          </h4>
                          <p className="text-[11px] text-soft-muted">
                            {sec.items?.length
                              ? `${sec.items.length} item(s)`
                              : "Summary / Raw content block"}
                          </p>
                        </div>
                      </div>

                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isIncluded
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        {isIncluded ? "Included in ATS Export" : "Excluded"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 4: ATS Audit & Transparent Scoring Breakdown */}
          {activeTab === "ats" && (
            <div className="space-y-4">
              <div className="surface p-4 rounded-2xl border border-white/80 space-y-1">
                <h3 className="text-xs font-bold text-soft-text flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  Transparent ATS Intelligence Audit
                </h3>
                <p className="text-[11px] text-soft-muted">
                  CareerPilot explainable algorithmic breakdown with byte-level extraction verification.
                </p>
              </div>

              {/* Strengths identified */}
              {atsAnalysis?.job_compatibility?.strengths?.length ? (
                <div className="surface p-4 rounded-2xl border border-emerald-200 bg-emerald-50/20 space-y-2">
                  <h4 className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    Verified Strengths & Positive Contributors
                  </h4>
                  <ul className="space-y-1.5 pl-5 list-disc text-xs text-emerald-800">
                    {atsAnalysis.job_compatibility.strengths.map((str, sIdx) => (
                      <li key={sIdx}>{str}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {/* Gaps detected */}
              {atsAnalysis?.job_compatibility?.gaps?.length ? (
                <div className="surface p-4 rounded-2xl border border-amber-200 bg-amber-50/20 space-y-2">
                  <h4 className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Role Gaps & Missing Evidence
                  </h4>
                  <ul className="space-y-1.5 pl-5 list-disc text-xs text-amber-800">
                    {atsAnalysis.job_compatibility.gaps.map((gap, gIdx) => (
                      <li key={gIdx}>{gap}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {/* Actionable recommendations */}
              {atsAnalysis?.job_compatibility?.recommendations?.length ? (
                <div className="surface p-4 rounded-2xl border border-blue-200 bg-blue-50/20 space-y-2">
                  <h4 className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-soft-blue" />
                    Actionable Recommendations to Elevate Fit
                  </h4>
                  <ul className="space-y-1.5 pl-5 list-disc text-xs text-blue-800">
                    {atsAnalysis.job_compatibility.recommendations.map((rec, rIdx) => (
                      <li key={rIdx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {/* Readability findings */}
              {atsAnalysis?.ats_readability?.findings?.length ? (
                <div className="surface p-4 rounded-2xl border border-slate-200 space-y-2">
                  <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <FileCheck className="w-4 h-4 text-slate-600" />
                    Parser Readability Diagnostics
                  </h4>
                  <ul className="space-y-1.5 pl-5 list-disc text-xs text-slate-600">
                    {atsAnalysis.ats_readability.findings.map((fnd, fIdx) => (
                      <li key={fIdx}>{fnd}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {/* Algorithmic Estimate Disclaimer */}
              <div className="well p-3.5 rounded-xl border border-white/60 text-[10px] text-soft-muted space-y-1">
                <p className="font-bold uppercase tracking-wider text-slate-400">Notice & Methodology Disclaimer</p>
                <p>
                  {atsAnalysis?.job_compatibility?.disclaimer ||
                    "CareerPilot Algorithmic Estimate. Calculated from factual candidate evidence matched against job requirements. Not an official hiring decision or black-box ATS guarantee."}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right Column (6 cols): Live ATS Single-Column Preview Canvas */}
        <div className="lg:col-span-6 sticky top-6">
          <div className="surface p-6 rounded-2xl space-y-4 border border-white/80">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/50">
              <span className="text-xs font-bold text-soft-text flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-soft-blue" />
                Live Single-Column ATS Canvas
              </span>
              <span className="text-[10px] uppercase font-bold text-soft-muted bg-slate-100 px-2 py-0.5 rounded">
                Real-Time IR Render
              </span>
            </div>

            {/* A4 Document Simulation Canvas */}
            <div className="bg-white rounded-xl p-8 shadow-inner border border-slate-200 min-h-[580px] max-h-[720px] overflow-y-auto space-y-5 text-slate-800 font-sans text-xs">
              {/* Candidate Header */}
              <div className="text-center space-y-1 pb-3 border-b border-slate-200">
                <h2 className="text-lg font-bold text-slate-900 tracking-tight uppercase">
                  {selectedResume?.tailored_content?.full_name ||
                    selectedResume?.tailored_content?.candidate_name ||
                    "Candidate Name"}
                </h2>
                <p className="text-[10px] text-slate-500">
                  {selectedResume?.tailored_content?.contact_info ||
                    "Verified Candidate Profile • CareerPilot Studio"}
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

                      {/* Bullets */}
                      {item.bullets?.length > 0 && (
                        <ul className="list-disc list-outside pl-4 space-y-1 pt-0.5">
                          {item.bullets.map((b: string, bIdx: number) => (
                            <li key={bIdx} className="text-[11px] leading-relaxed text-slate-700">
                              {b}
                            </li>
                          ))}
                        </ul>
                      )}

                      {/* Description / Text line if item has no bullets */}
                      {(!item.bullets || item.bullets.length === 0) && item.description && (
                        <p className="text-[11px] leading-relaxed text-slate-700 whitespace-pre-line pt-0.5">
                          {item.description}
                        </p>
                      )}
                    </div>
                  ))}

                  {/* Raw content block (e.g. skills or summary) */}
                  {!sec.items?.length && sec.raw_content && (
                    <div className="text-[11px] leading-relaxed text-slate-700 whitespace-pre-line">
                      {sec.raw_content}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Add Custom Evidence Modal */}
      {evidenceModalReq && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="surface p-6 rounded-2xl max-w-lg w-full space-y-4 border border-white/80 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-soft-text flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                Attach Verified Career Evidence
              </h3>
              <button
                onClick={() => setEvidenceModalReq(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="well p-3 rounded-xl border border-white/60 space-y-1 text-xs">
              <span className="text-[10px] font-bold uppercase text-soft-muted">Target Requirement</span>
              <p className="font-semibold text-soft-text">{evidenceModalReq.requirement_text}</p>
            </div>

            <form onSubmit={handleAddCustomEvidenceSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Verifiable Achievement / Experience Detail *
                </label>
                <textarea
                  rows={4}
                  value={customEvidenceText}
                  onChange={(e) => setCustomEvidenceText(e.target.value)}
                  placeholder="Describe your concrete experience, responsibilities, or measurable outcome for this competency..."
                  className="w-full text-xs rounded-xl well border border-white/60 p-3 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue resize-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                  Repository / Artifact URL (Optional)
                </label>
                <input
                  type="url"
                  value={customEvidenceUrl}
                  onChange={(e) => setCustomEvidenceUrl(e.target.value)}
                  placeholder="https://github.com/your-username/repo-name"
                  className="w-full text-xs rounded-xl well border border-white/60 p-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                />
                <p className="text-[10px] text-soft-muted mt-1">
                  Submissions are server-classified as self-attested evidence (pending independent verification).
                </p>
              </div>

              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setEvidenceModalReq(null)}
                  className="btn-soft px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingEvidence || !customEvidenceText.trim()}
                  className="btn-primary px-5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {submittingEvidence ? "Saving & Auditing..." : "Attach & Recalculate Fit"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
                      Analyzing Requirements & Tailoring...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Generate Tailored Resume
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
