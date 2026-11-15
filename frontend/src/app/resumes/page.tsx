"use client";

import React, { useEffect, useState, useRef } from "react";
import {
  FileUp,
  FileText,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Trash2,
  Star,
  Edit3,
  Layers,
  ChevronDown,
  ChevronUp,
  Eye,
  Save,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  listUserResumes,
  getResumeDetail,
  uploadResumeFile,
  updateResumeSections,
  setMasterResume,
  deleteResume,
  buildCandidateProfile,
  ResumeListItem,
  ResumeDetail,
  ResumeSection,
} from "@/lib/api";

export default function ResumesPage() {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [selectedResume, setSelectedResume] = useState<ResumeDetail | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadPhase, setUploadPhase] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isMasterUpload, setIsMasterUpload] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});
  const [editableSections, setEditableSections] = useState<Record<string, { heading: string; raw_content: string }>>({});
  const [savingSections, setSavingSections] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    setLoadingList(true);
    try {
      const data = await listUserResumes();
      setResumes(data);
      if (data.length > 0 && !selectedResume) {
        loadDetail(data[0].id);
      }
    } catch (err: any) {
      if (!err.message?.includes("Authentication required") && !err.message?.includes("Not authenticated")) {
        setStatusMessage({ type: "error", text: err.message || "Failed to fetch resumes." });
      }
    } finally {
      setLoadingList(false);
    }
  };

  const loadDetail = async (id: string) => {
    setLoadingDetail(true);
    try {
      const detail = await getResumeDetail(id);
      setSelectedResume(detail);

      // Initialize edit state and expand all sections by default
      const initialEdits: Record<string, { heading: string; raw_content: string }> = {};
      const initialExp: Record<string, boolean> = {};
      detail.sections.forEach((s) => {
        initialEdits[s.id] = { heading: s.heading, raw_content: s.raw_content };
        initialExp[s.id] = true;
      });
      setEditableSections(initialEdits);
      setExpandedSections(initialExp);
    } catch {
      setStatusMessage({ type: "error", text: "Failed to load resume details." });
    } finally {
      setLoadingDetail(false);
    }
  };

  const processFile = async (file: File) => {
    // 1. Validate file extension
    const name = file.name.toLowerCase();
    if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
      setStatusMessage({
        type: "error",
        text: "Unsupported file format. Please upload a PDF or DOCX file.",
      });
      return;
    }

    // 2. Validate file size (10 MB)
    if (file.size > 10 * 1024 * 1024) {
      setStatusMessage({
        type: "error",
        text: `File exceeds 10 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`,
      });
      return;
    }

    setUploading(true);
    setUploadPhase("Uploading and segmenting sections...");
    setStatusMessage(null);

    try {
      // 1. Ingest & Segment Resume
      const result = await uploadResumeFile(file, isMasterUpload);

      // 2. Automatically sync competencies into Candidate Profile
      setUploadPhase("Syncing extracted competencies into Candidate Profile...");
      let skillCount = 0;
      try {
        const skills = await buildCandidateProfile(result.resume_id);
        skillCount = skills.length;
      } catch (syncErr: any) {
        console.warn("Auto-syncing candidate profile warning:", syncErr);
      }

      setStatusMessage({
        type: "success",
        text: `Successfully ingested ${result.file_name}: ${result.sections_detected} sections detected and ${skillCount} competencies anchored with evidence!`,
      });
      await loadResumes();
      await loadDetail(result.resume_id);
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Upload failed." });
    } finally {
      setUploading(false);
      setUploadPhase(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (uploading) return;
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleToggleSection = (sectionId: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [sectionId]: !prev[sectionId],
    }));
  };

  const handleSectionTextChange = (sectionId: string, field: "heading" | "raw_content", value: string) => {
    setEditableSections((prev) => ({
      ...prev,
      [sectionId]: {
        ...prev[sectionId],
        [field]: value,
      },
    }));
  };

  const handleSaveChanges = async () => {
    if (!selectedResume) return;
    setSavingSections(true);

    try {
      const payload = Object.entries(editableSections).map(([id, data]) => ({
        id,
        heading: data.heading,
        raw_content: data.raw_content,
      }));
      const updated = await updateResumeSections(selectedResume.id, payload);
      setSelectedResume(updated);
      setStatusMessage({ type: "success", text: "Parsed sections successfully updated!" });
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Failed to update sections." });
    } finally {
      setSavingSections(false);
    }
  };

  const handleSetMaster = async (id: string) => {
    try {
      await setMasterResume(id);
      setStatusMessage({ type: "success", text: "Designated as active Master Profile!" });
      await loadResumes();
      if (selectedResume?.id === id) {
        setSelectedResume((prev) => (prev ? { ...prev, is_master: true } : null));
      }
    } catch {
      setStatusMessage({ type: "error", text: "Failed to set master resume." });
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this resume?")) return;
    try {
      await deleteResume(id);
      setStatusMessage({ type: "success", text: "Resume successfully deleted." });
      if (selectedResume?.id === id) {
        setSelectedResume(null);
      }
      await loadResumes();
    } catch {
      setStatusMessage({ type: "error", text: "Failed to delete resume." });
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/60 pb-3">
        <div>
          <h1 className="text-2xl font-extrabold text-soft-text">Resume Ingestion & Parsing</h1>
          <p className="text-xs text-soft-muted">
            Upload PDF or DOCX resumes with automatic OCR fallback, section segmentation, and review editor.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="info">Dual Engine: pdfplumber + OCR</Badge>
          <Badge variant="success">Factual Extraction</Badge>
        </div>
      </div>

      {/* Global Status Message */}
      {statusMessage && (
        <div
          className={`well p-3 flex items-center gap-2 text-xs border ${
            statusMessage.type === "success"
              ? "text-soft-green-text border-green-200"
              : "text-soft-orange-text border-orange-200"
          }`}
        >
          {statusMessage.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* 2-Column Split Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols): Upload Dropzone & Resumes List */}
        <div className="lg:col-span-5 space-y-6">
          {/* Dropzone Card */}
          <Card variant="surface">
            <CardHeader>
              <CardTitle className="text-base">Upload Document</CardTitle>
              <CardDescription>Accepts PDF or DOCX files up to 10 MB</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`well p-8 text-center cursor-pointer border-2 border-dashed transition-all group space-y-2 select-none ${
                  isDragging
                    ? "border-soft-blue bg-soft-blue/10 scale-[1.01]"
                    : "border-slate-300 hover:border-soft-blue"
                }`}
              >
                <div className={`w-12 h-12 rounded-full surface mx-auto flex items-center justify-center text-soft-blue transition-transform ${isDragging ? "scale-110" : "group-hover:scale-105"}`}>
                  {uploading ? (
                    <RefreshCw className="w-6 h-6 animate-spin" />
                  ) : (
                    <FileUp className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <p className="text-xs font-bold text-soft-text">
                    {uploading
                      ? (uploadPhase || "Extracting & Segmenting...")
                      : isDragging
                      ? "Release file here to upload"
                      : "Click or drag resume here"}
                  </p>
                  <p className="text-[11px] text-soft-muted">PDF or DOCX (Single or Multi-page up to 10 MB)</p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                />
              </div>

              {/* Master Checkbox */}
              <div className="flex items-center gap-2 text-xs text-soft-text px-1">
                <input
                  type="checkbox"
                  id="master-check"
                  checked={isMasterUpload}
                  onChange={(e) => setIsMasterUpload(e.target.checked)}
                  className="rounded text-soft-blue focus:ring-soft-blue"
                />
                <label htmlFor="master-check" className="cursor-pointer font-medium">
                  Designate as Master Profile Resume
                </label>
              </div>
            </CardContent>
          </Card>

          {/* Uploaded Resumes Library */}
          <Card variant="surface">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Uploaded Resumes</CardTitle>
                <span className="text-xs text-soft-muted font-bold">{resumes.length} Files</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {loadingList ? (
                <div className="well p-4 skeleton-well h-32" />
              ) : resumes.length === 0 ? (
                <div className="well p-6 text-center text-xs text-soft-muted space-y-1">
                  <FileText className="w-8 h-8 text-slate-400 mx-auto" />
                  <p className="font-semibold text-soft-text">No resumes uploaded yet</p>
                  <p>Upload your existing resume above to begin extraction.</p>
                </div>
              ) : (
                resumes.map((r) => (
                  <div
                    key={r.id}
                    className={`well p-3.5 space-y-2.5 transition-all cursor-pointer ${
                      selectedResume?.id === r.id ? "border-l-4 border-l-soft-blue bg-white/40" : ""
                    }`}
                    onClick={() => loadDetail(r.id)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-soft-text truncate max-w-[200px]">
                            {r.file_name}
                          </span>
                          <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 bg-slate-200 rounded">
                            {r.file_format}
                          </span>
                        </div>
                        <p className="text-[11px] text-soft-muted">
                          {(r.file_size_bytes / 1024).toFixed(1)} KB • {r.sections_count} sections detected
                        </p>
                      </div>
                      <div className="flex items-center gap-1">
                        {r.is_master && (
                          <Badge variant="success" className="text-[10px] py-0">
                            Master
                          </Badge>
                        )}
                        {r.ocr_applied && (
                          <Badge variant="warning" className="text-[10px] py-0">
                            OCR
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 text-xs">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSetMaster(r.id);
                        }}
                        className="text-[11px] text-soft-blue hover:underline flex items-center gap-1"
                      >
                        <Star className="w-3 h-3" />
                        {r.is_master ? "Active Master" : "Set as Master"}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(r.id);
                        }}
                        className="text-[11px] text-soft-orange-text hover:underline flex items-center gap-1"
                      >
                        <Trash2 className="w-3 h-3" />
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column (7 cols): Parsed Section Review & Correction Editor */}
        <div className="lg:col-span-7 space-y-4">
          <Card variant="surface">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Layers className="w-4 h-4 text-soft-blue" />
                    Parsed Section Review & Editor
                  </CardTitle>
                  <CardDescription>
                    Review detected sections and correct any extraction errors before matching
                  </CardDescription>
                </div>
                {selectedResume && (
                  <Button
                    onClick={handleSaveChanges}
                    variant="primary"
                    size="sm"
                    disabled={savingSections}
                    className="flex items-center gap-1.5"
                  >
                    {savingSections ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Save className="w-3.5 h-3.5" />
                    )}
                    Save Changes
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {loadingDetail ? (
                <div className="space-y-3">
                  <div className="well p-4 skeleton-well h-24" />
                  <div className="well p-4 skeleton-well h-36" />
                  <div className="well p-4 skeleton-well h-28" />
                </div>
              ) : !selectedResume ? (
                <div className="well p-12 text-center text-xs text-soft-muted space-y-2">
                  <Eye className="w-10 h-10 text-slate-400 mx-auto" />
                  <p className="font-bold text-soft-text text-sm">Select or upload a resume to review</p>
                  <p>Detected sections and extracted bullet achievements will appear here.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* File Info Strip */}
                  <div className="well p-3 flex items-center justify-between text-xs">
                    <span className="font-bold text-soft-text">
                      Active: {selectedResume.file_name}
                    </span>
                    <span className="text-soft-muted">
                      Uploaded on {new Date(selectedResume.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  {/* Sections Accordion Stack */}
                  <div className="space-y-3">
                    {selectedResume.sections.map((section: ResumeSection) => {
                      const isExpanded = expandedSections[section.id] ?? true;
                      const editState = editableSections[section.id] || {
                        heading: section.heading,
                        raw_content: section.raw_content,
                      };

                      return (
                        <div key={section.id} className="surface p-4 space-y-3">
                          {/* Accordion Header */}
                          <div
                            className="flex items-center justify-between cursor-pointer select-none"
                            onClick={() => handleToggleSection(section.id)}
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-sm text-soft-text">
                                {editState.heading || section.heading}
                              </span>
                              <Badge variant="info" className="text-[10px] py-0 uppercase">
                                {section.section_type}
                              </Badge>
                              {section.items.length > 0 && (
                                <Badge variant="neutral" className="text-[10px] py-0">
                                  {section.items.length} items
                                </Badge>
                              )}
                            </div>
                            <button className="p-1 hover:bg-slate-200/50 rounded text-soft-muted">
                              {isExpanded ? (
                                <ChevronUp className="w-4 h-4" />
                              ) : (
                                <ChevronDown className="w-4 h-4" />
                              )}
                            </button>
                          </div>

                          {/* Accordion Body */}
                          {isExpanded && (
                            <div className="space-y-3 pt-2 border-t border-slate-200/60">
                              {/* Heading Input */}
                              <div className="space-y-1">
                                <label className="text-[11px] font-bold text-soft-muted uppercase">
                                  Section Title
                                </label>
                                <input
                                  type="text"
                                  value={editState.heading}
                                  onChange={(e) =>
                                    handleSectionTextChange(section.id, "heading", e.target.value)
                                  }
                                  className="input-well w-full text-xs py-1.5 px-3"
                                />
                              </div>

                              {/* Content Textarea */}
                              <div className="space-y-1">
                                <label className="text-[11px] font-bold text-soft-muted uppercase">
                                  Section Raw Text
                                </label>
                                <textarea
                                  rows={4}
                                  value={editState.raw_content}
                                  onChange={(e) =>
                                    handleSectionTextChange(section.id, "raw_content", e.target.value)
                                  }
                                  className="input-well w-full text-xs py-2 px-3 leading-relaxed font-mono"
                                />
                              </div>

                              {/* Structured Extracted Items Preview */}
                              {section.items.length > 0 && (
                                <div className="space-y-2 pt-1">
                                  <label className="text-[11px] font-bold text-soft-muted uppercase">
                                    Detected Structured Items & Bullets
                                  </label>
                                  <div className="space-y-2">
                                    {section.items.map((item) => (
                                      <div key={item.id} className="well p-2.5 text-xs space-y-1">
                                        <div className="flex items-center justify-between">
                                          <span className="font-bold text-soft-text">
                                            {item.title}
                                            {item.organization ? ` @ ${item.organization}` : ""}
                                          </span>
                                          <Badge variant="neutral" className="text-[10px]">
                                            {item.item_type}
                                          </Badge>
                                        </div>
                                        {item.bullets.length > 0 && (
                                          <ul className="list-disc list-inside space-y-0.5 text-soft-muted text-[11px] pl-1">
                                            {item.bullets.map((b: string, bIdx: number) => (
                                              <li key={bIdx}>{b}</li>
                                            ))}
                                          </ul>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
