import { getStoredToken } from "./auth";

export interface SystemHealth {
  status: string;
  service: string;
  environment: string;
  version: string;
}

export interface OllamaStatus {
  provider: string;
  is_available: boolean;
  base_url: string;
  active_model: string;
  available_models: string[];
  error?: string | null;
}

export interface LLMSettings {
  provider: string;
  is_free_mode: boolean;
  ollama_base_url: string;
  default_model: string;
  fallback_model: string;
  has_cloud_fallback: boolean;
  daemon_status: OllamaStatus;
}

export interface ResumeItem {
  id: string;
  section_id: string;
  item_type: string;
  title: string;
  organization?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  bullets: any[];
  created_at: string;
}

export interface ResumeSection {
  id: string;
  resume_id: string;
  section_type: string;
  heading: string;
  raw_content: string;
  display_order: number;
  items: ResumeItem[];
  created_at: string;
}

export interface ResumeDetail {
  id: string;
  user_id: string;
  file_name: string;
  file_key: string;
  file_format: string;
  file_size_bytes: number;
  raw_text: string;
  is_master: boolean;
  parsing_status: string;
  ocr_applied: boolean;
  created_at: string;
  updated_at: string;
  sections: ResumeSection[];
}

export interface ResumeListItem {
  id: string;
  file_name: string;
  file_format: string;
  file_size_bytes: number;
  is_master: boolean;
  parsing_status: string;
  ocr_applied: boolean;
  sections_count: number;
  created_at: string;
}

export interface ResumeUploadResult {
  resume_id: string;
  file_name: string;
  file_format: string;
  status: string;
  is_master: boolean;
  ocr_applied: boolean;
  sections_detected: number;
  message: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function authHeader(): Record<string, string> {
  const token = getStoredToken();
  if (!token || token === "undefined" || token === "null" || token.trim() === "") {
    return {};
  }
  return { Authorization: `Bearer ${token}` };
}

export function handle401(): void {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("careerpilot:unauthorized"));
  }
}

export async function parseApiError(res: Response, defaultMsg: string = "Request failed"): Promise<string> {
  try {
    const data = await res.json();
    if (data.detail) {
      if (typeof data.detail === "string") return data.detail;
      if (Array.isArray(data.detail)) {
        return data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(", ");
      }
    }
    if (data.error?.message) return data.error.message;
    if (data.message) return data.message;
  } catch {
    // Non-JSON or empty response body
  }
  if (res.status === 401) return "Authentication required. Please sign in to your workspace.";
  if (res.status === 403) return "Access denied. You do not have permission for this resource.";
  if (res.status === 404) return "Requested resource was not found.";
  if (res.status >= 500) return "An unexpected server error occurred. Please try again.";
  return `${defaultMsg} (HTTP ${res.status})`;
}

export async function getSystemHealth(): Promise<SystemHealth> {
  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return {
      status: "offline",
      service: "CareerPilot",
      environment: "development",
      version: "1.0.0-phase0",
    };
  }
}

export async function getOllamaStatus(): Promise<OllamaStatus> {
  try {
    const res = await fetch(`${API_BASE}/health/ollama`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return {
      provider: "ollama",
      is_available: false,
      base_url: "http://localhost:11434",
      active_model: "llama3.1:8b",
      available_models: [],
      error: "Backend API offline or unreachable",
    };
  }
}

export async function getLLMSettings(): Promise<LLMSettings | null> {
  try {
    const res = await fetch(`${API_BASE}/settings/llm`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return null;
  }
}

// ==============================================================================
// Resume API Client
// ==============================================================================

export async function uploadResumeFile(
  file: File,
  isMaster: boolean = false
): Promise<ResumeUploadResult> {
  const token = getStoredToken();
  if (!token) {
    handle401();
    throw new Error("Authentication required. Please sign in to upload a resume.");
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("is_master", String(isMaster));

  const res = await fetch(`${API_BASE}/resumes/upload`, {
    method: "POST",
    headers: {
      ...authHeader(),
    },
    body: formData,
  });

  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication session expired. Please sign in again.");
    }
    const err = await parseApiError(res, "Failed to upload and parse resume.");
    throw new Error(err);
  }
  return await res.json();
}

export async function listUserResumes(): Promise<ResumeListItem[]> {
  const res = await fetch(`${API_BASE}/resumes`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication required. Please sign in to view resumes.");
    }
    const msg = await parseApiError(res, "Failed to fetch resumes");
    throw new Error(msg);
  }
  return await res.json();
}

export async function getResumeDetail(resumeId: string): Promise<ResumeDetail> {
  const res = await fetch(`${API_BASE}/resumes/${resumeId}`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to load resume details");
  }
  return await res.json();
}

export async function updateResumeSections(
  resumeId: string,
  sections: Array<{ id: string; heading?: string; raw_content?: string; section_type?: string }>
): Promise<ResumeDetail> {
  const res = await fetch(`${API_BASE}/resumes/${resumeId}/sections`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ sections }),
  });
  if (!res.ok) {
    throw new Error("Failed to update sections");
  }
  return await res.json();
}

export async function setMasterResume(resumeId: string): Promise<ResumeDetail> {
  const res = await fetch(`${API_BASE}/resumes/${resumeId}/set-master`, {
    method: "PUT",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to set master resume");
  }
  return await res.json();
}

export async function deleteResume(resumeId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/resumes/${resumeId}`, {
    method: "DELETE",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to delete resume");
  }
}


// ==============================================================================
// Job Description & Candidate Intelligence API Client
// ==============================================================================

export interface JDRequirement {
  id: string;
  jd_id: string;
  requirement_text: string;
  category: string;
  is_mandatory: boolean;
  importance_weight: number;
  min_years_experience?: number | null;
  canonical_skill_name?: string | null;
  created_at: string;
}

export interface JobDescription {
  id: string;
  user_id: string;
  job_title: string;
  company_name?: string | null;
  department?: string | null;
  seniority_level?: string | null;
  work_mode?: string | null;
  location?: string | null;
  salary_range?: string | null;
  raw_text: string;
  requirements: JDRequirement[];
  created_at: string;
}

export interface JobDescriptionSummary {
  id: string;
  user_id: string;
  job_title: string;
  company_name?: string | null;
  seniority_level?: string | null;
  work_mode?: string | null;
  location?: string | null;
  requirements_count: number;
  created_at: string;
}

export interface CandidateSkill {
  id: string;
  user_id: string;
  skill_name: string;
  normalized_name: string;
  category: string;
  proficiency_level?: string | null;
  years_experience?: number | null;
  evidence_text?: string | null;
  evidence_item_id?: string | null;
  is_user_verified: boolean;
  created_at: string;
}

export async function analyzeJob(data: {
  raw_text: string;
  job_title?: string;
  company_name?: string;
}): Promise<JobDescription> {
  const res = await fetch(`${API_BASE}/jobs/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to analyze job description.");
  }
  return await res.json();
}

export async function listJobs(): Promise<JobDescriptionSummary[]> {
  const res = await fetch(`${API_BASE}/jobs`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication required. Please sign in.");
    }
    const err = await parseApiError(res, "Failed to fetch jobs list.");
    throw new Error(err);
  }
  return await res.json();
}

export async function getJobDetail(jobId: string): Promise<JobDescription> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to load job details.");
  }
  return await res.json();
}

export async function deleteJob(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`, {
    method: "DELETE",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to delete job description.");
  }
}

export async function buildCandidateProfile(resumeId?: string): Promise<CandidateSkill[]> {
  const token = getStoredToken();
  if (!token) {
    handle401();
    throw new Error("Authentication required. Please sign in to sync candidate profile.");
  }

  const res = await fetch(`${API_BASE}/candidate/build-profile`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ resume_id: resumeId || null }),
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication session expired. Please sign in again.");
    }
    const err = await parseApiError(res, "Failed to build candidate profile.");
    throw new Error(err);
  }
  return await res.json();
}

export async function getCandidateProfile(): Promise<CandidateSkill[]> {
  const res = await fetch(`${API_BASE}/candidate/profile`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication required. Please sign in.");
    }
    const err = await parseApiError(res, "Failed to load candidate profile.");
    throw new Error(err);
  }
  return await res.json();
}

export async function verifyCandidateSkill(
  skillId: string,
  isVerified: boolean = true
): Promise<CandidateSkill> {
  const res = await fetch(`${API_BASE}/candidate/verify-skill`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ skill_id: skillId, is_verified: isVerified }),
  });
  if (!res.ok) {
    throw new Error("Failed to verify skill.");
  }
  return await res.json();
}

export async function addCustomSkill(data: {
  skill_name: string;
  category?: string;
  proficiency_level?: string;
  evidence_text?: string;
}): Promise<CandidateSkill> {
  const res = await fetch(`${API_BASE}/candidate/skills`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to add custom skill.");
  }
  return await res.json();
}

export async function deleteCandidateSkill(skillId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/candidate/skills/${skillId}`, {
    method: "DELETE",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to remove skill.");
  }
}


// ==============================================================================
// Candidate-Role Matching & Skill Gaps API Client
// ==============================================================================

export interface SkillGapItem {
  id: string;
  match_evaluation_id: string;
  requirement_id: string;
  requirement_text?: string | null;
  category?: string | null;
  is_mandatory?: boolean | null;
  status: "DEMONSTRATED" | "PARTIAL" | "NOT_DEMONSTRATED" | "REQUIRES_VERIFICATION" | string;
  gap_severity: "CRITICAL" | "MODERATE" | "LOW" | string;
  evidence_snippet?: string | null;
  similarity_score?: number | null;
  suggested_action?: string | null;
  is_resolved: boolean;
  created_at: string;
}

export interface SubScores {
  skill_match: number;
  semantic_similarity: number;
  lexical_bm25: number;
  experience_depth: number;
  domain_relevance: number;
}

export interface MatchEvaluation {
  id: string;
  user_id: string;
  resume_id: string;
  jd_id: string;
  job_title: string;
  company_name?: string | null;
  overall_score: number;
  rating_label: string;
  sub_scores: SubScores;
  scoring_breakdown: Record<string, any>;
  summary_analysis?: string | null;
  gap_items: SkillGapItem[];
  created_at: string;
}

export interface MatchSummary {
  id: string;
  user_id: string;
  resume_id: string;
  jd_id: string;
  job_title: string;
  company_name?: string | null;
  overall_score: number;
  rating_label: string;
  created_at: string;
}

export async function evaluateMatch(data: {
  resume_id: string;
  jd_id: string;
}): Promise<MatchEvaluation> {
  const res = await fetch(`${API_BASE}/matches/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to trigger match evaluation.");
  }
  return await res.json();
}

export async function listMatches(): Promise<MatchSummary[]> {
  const res = await fetch(`${API_BASE}/matches`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication required. Please sign in.");
    }
    const err = await parseApiError(res, "Failed to load match evaluations.");
    throw new Error(err);
  }
  return await res.json();
}

export async function getMatchDetail(matchId: string): Promise<MatchEvaluation> {
  const res = await fetch(`${API_BASE}/matches/${matchId}`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to load match report details.");
  }
  return await res.json();
}

export async function verifyMatchGap(
  matchId: string,
  data: {
    gap_item_id: string;
    has_experience?: boolean;
    years_experience?: number;
    verification_evidence?: string;
  }
): Promise<MatchEvaluation> {
  const res = await fetch(`${API_BASE}/matches/${matchId}/gaps/verify`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to verify requirement gap.");
  }
  return await res.json();
}

export async function deleteMatch(matchId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/matches/${matchId}`, {
    method: "DELETE",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to delete match evaluation.");
  }
}


// ==============================================================================
// AI Resume Optimizer & Live Editor API Client
// ==============================================================================

export interface RequirementEvidenceMapping {
  requirement_id: string;
  requirement_text: string;
  is_mandatory: boolean;
  canonical_skill_name?: string | null;
  category?: string | null;
  matched_section_id?: string | null;
  matched_section_name?: string | null;
  matched_item_id?: string | null;
  matched_bullet_index?: number | null;
  original_evidence_text?: string | null;
  matching_method: "ONTOLOGY_EXACT" | "DENSE_OLLAMA" | "LEXICAL_BM25_FALLBACK" | "DENSE_HASH_FALLBACK" | string;
  confidence_score: number;
  verification_status: "CANDIDATE_VERIFIED" | "EXTRACTED_UNCONFIRMED" | "UNMATCHED" | string;
}

export interface MissingRequirementItem {
  requirement_id: string;
  requirement_text: string;
  is_mandatory: boolean;
  canonical_skill_name?: string | null;
  category?: string | null;
  suggested_action: string;
}

export interface ContentSelectionItem {
  section_id: string;
  section_type: string;
  heading: string;
  item_id?: string | null;
  bullet_index?: number | null;
  content_text: string;
  decision: "INCLUDED" | "PROPOSED_REWRITE" | "REORDERED" | "EXCLUDED" | "MISSING_INFO" | string;
  relevance_score: number;
  matched_requirement_ids: string[];
  reasoning: string;
}

export interface ResumeCompositionIR {
  candidate_identity: Record<string, any>;
  sections: any[];
  export_sections: any[];
  provenance: any[];
  metadata: Record<string, any>;
  requirement_mappings: RequirementEvidenceMapping[];
  missing_requirements: MissingRequirementItem[];
}

export interface TailoredBulletDiff {
  id: string;
  tailored_resume_id: string;
  section_id?: string | null;
  item_id?: string | null;
  bullet_index: number;
  original_text: string;
  optimized_text: string;
  rationale: string;
  targeted_requirement_id?: string | null;
  nli_verification_status: "VERIFIED" | "ENTAILMENT" | "NEUTRAL" | "FLAGGED" | "REQUIRES_REVIEW" | "NOT_VERIFIED" | string;
  status: "PENDING" | "ACCEPTED" | "REJECTED" | "EDITED" | "RESTORED" | string;
  edited_text?: string | null;
  created_at: string;
}

export interface TailoredResume {
  id: string;
  user_id: string;
  source_resume_id: string;
  target_jd_id: string;
  version_title: string;
  job_title?: string | null;
  company_name?: string | null;
  tailored_content: Record<string, any>;
  diffs_count: number;
  diffs: TailoredBulletDiff[];
  created_at: string;
  updated_at: string;
}

export interface TailoredResumeSummary {
  id: string;
  user_id: string;
  source_resume_id: string;
  target_jd_id: string;
  version_title: string;
  job_title?: string | null;
  company_name?: string | null;
  diffs_count: number;
  created_at: string;
}

export async function tailorResume(data: {
  resume_id: string;
  jd_id: string;
}): Promise<TailoredResume> {
  const res = await fetch(`${API_BASE}/optimizer/tailor`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to tailor resume.");
  }
  return await res.json();
}

export async function listTailoredResumes(): Promise<TailoredResumeSummary[]> {
  const res = await fetch(`${API_BASE}/optimizer/tailored-resumes`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication required. Please sign in.");
    }
    const err = await parseApiError(res, "Failed to load tailored resumes list.");
    throw new Error(err);
  }
  return await res.json();
}

export async function getTailoredResume(id: string): Promise<TailoredResume> {
  const res = await fetch(`${API_BASE}/optimizer/tailored-resumes/${id}`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to load tailored resume details.");
  }
  return await res.json();
}

export async function updateDiff(
  diffId: string,
  data: { status: string; edited_text?: string }
): Promise<TailoredBulletDiff> {
  const res = await fetch(`${API_BASE}/optimizer/diffs/${diffId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update bullet diff.");
  }
  return await res.json();
}

export async function restoreDiff(diffId: string): Promise<TailoredBulletDiff> {
  const res = await fetch(`${API_BASE}/optimizer/diffs/${diffId}/restore`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to restore bullet diff.");
  }
  return await res.json();
}

export async function toggleSectionVisibility(
  tailoredId: string,
  sectionId: string,
  isIncluded: boolean,
  displayOrder?: number
): Promise<TailoredResume> {
  const res = await fetch(`${API_BASE}/optimizer/tailored-resumes/${tailoredId}/sections`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({
      section_id: sectionId,
      is_included: isIncluded,
      display_order: displayOrder,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update section visibility.");
  }
  return await res.json();
}

export async function getCompositionIR(tailoredId: string): Promise<ResumeCompositionIR> {
  const res = await fetch(`${API_BASE}/optimizer/tailored-resumes/${tailoredId}/composition`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to load composition IR.");
  }
  return await res.json();
}

export async function exportPDF(tailoredId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/optimizer/tailored-resumes/${tailoredId}/export-pdf`, {
    method: "POST",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to generate PDF export.");
  }
  return await res.blob();
}

export async function exportDOCX(tailoredId: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/optimizer/tailored-resumes/${tailoredId}/export-docx`, {
    method: "POST",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to generate DOCX export.");
  }
  return await res.blob();
}

export async function deleteTailoredResume(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/optimizer/tailored-resumes/${id}`, {
    method: "DELETE",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to delete tailored resume.");
  }
}

// ==========================================
// Phase 6: Learning Roadmaps & Interview Intelligence
// ==========================================

export interface CuratedResource {
  title: string;
  url: string;
  type: string;
}

export interface LearningMilestone {
  id: string;
  roadmap_id: string;
  sequence_order: number;
  skill_name: string;
  milestone_title: string;
  description: string;
  curated_resources: CuratedResource[];
  practical_project_brief?: string | null;
  is_completed: boolean;
  created_at: string;
}

export interface LearningRoadmap {
  id: string;
  user_id: string;
  match_evaluation_id: string;
  target_role_title: string;
  estimated_total_hours: number;
  status: string;
  milestones: LearningMilestone[];
  completed_count: number;
  total_milestones: number;
  created_at: string;
}

export interface LearningRoadmapSummary {
  id: string;
  user_id: string;
  match_evaluation_id: string;
  target_role_title: string;
  estimated_total_hours: number;
  status: string;
  milestones_count: number;
  created_at: string;
}

export interface StarGuidelines {
  situation?: string;
  task?: string;
  action?: string;
  result?: string;
}

export interface InterviewFeedback {
  score: number;
  strengths: string[];
  improvements: string[];
  critique: string;
}

export interface InterviewQuestion {
  id: string;
  prep_id: string;
  question_type: "TECHNICAL" | "BEHAVIORAL_STAR" | "GAP_DEFENSE" | string;
  question_text: string;
  target_skill_or_gap?: string | null;
  evaluation_criteria: string;
  star_guidelines: StarGuidelines;
  practice_response?: string | null;
  ai_feedback?: InterviewFeedback | null;
  created_at: string;
}

export interface InterviewPrep {
  id: string;
  user_id: string;
  match_evaluation_id: string;
  target_role_title: string;
  company_name?: string | null;
  questions_count: number;
  questions: InterviewQuestion[];
  created_at: string;
}

export interface InterviewPrepSummary {
  id: string;
  user_id: string;
  match_evaluation_id: string;
  target_role_title: string;
  company_name?: string | null;
  questions_count: number;
  created_at: string;
}

export async function generateRoadmap(matchEvaluationId: string): Promise<LearningRoadmap> {
  const res = await fetch(`${API_BASE}/learning/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ match_evaluation_id: matchEvaluationId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate learning roadmap.");
  }
  return await res.json();
}

export async function listRoadmaps(): Promise<LearningRoadmapSummary[]> {
  const res = await fetch(`${API_BASE}/learning`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication required. Please sign in.");
    }
    const err = await parseApiError(res, "Failed to load learning roadmaps.");
    throw new Error(err);
  }
  return await res.json();
}

export async function getRoadmap(id: string): Promise<LearningRoadmap> {
  const res = await fetch(`${API_BASE}/learning/${id}`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to load learning roadmap.");
  }
  return await res.json();
}

export async function toggleMilestone(
  milestoneId: string,
  isCompleted: boolean
): Promise<LearningMilestone> {
  const res = await fetch(`${API_BASE}/learning/milestones/${milestoneId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ is_completed: isCompleted }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update milestone.");
  }
  return await res.json();
}

export async function deleteRoadmap(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/learning/${id}`, {
    method: "DELETE",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to delete learning roadmap.");
  }
}

export async function generateInterviewPrep(matchEvaluationId: string): Promise<InterviewPrep> {
  const res = await fetch(`${API_BASE}/interview/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ match_evaluation_id: matchEvaluationId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to generate interview preparation.");
  }
  return await res.json();
}

export async function listInterviewPreps(): Promise<InterviewPrepSummary[]> {
  const res = await fetch(`${API_BASE}/interview`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication required. Please sign in.");
    }
    const err = await parseApiError(res, "Failed to load interview preparations.");
    throw new Error(err);
  }
  return await res.json();
}

export async function getInterviewPrep(id: string): Promise<InterviewPrep> {
  const res = await fetch(`${API_BASE}/interview/${id}`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to load interview preparation.");
  }
  return await res.json();
}

export async function evaluateInterviewAnswer(
  questionId: string,
  practiceResponse: string
): Promise<InterviewQuestion> {
  const res = await fetch(`${API_BASE}/interview/questions/${questionId}/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ practice_response: practiceResponse }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to evaluate interview answer.");
  }
  return await res.json();
}

export async function deleteInterviewPrep(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/interview/${id}`, {
    method: "DELETE",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to delete interview preparation.");
  }
}

// ==========================================
// Phase 7: Application Pipeline & Tracker
// ==========================================

export interface ApplicationActivity {
  id: string;
  activity_type: string;
  from_stage?: string | null;
  to_stage?: string | null;
  note?: string | null;
  created_at: string;
}

export interface JobApplication {
  id: string;
  user_id: string;
  job_description_id?: string | null;
  tailored_resume_id?: string | null;
  match_evaluation_id?: string | null;
  company_name: string;
  job_title: string;
  location?: string | null;
  stage: string;
  priority: string;
  salary_range?: string | null;
  job_url?: string | null;
  applied_date?: string | null;
  deadline?: string | null;
  notes?: string | null;
  is_archived: boolean;
  match_score?: number | null;
  tailored_resume_title?: string | null;
  activities: ApplicationActivity[];
  created_at: string;
  updated_at: string;
}

export interface JobApplicationSummary {
  id: string;
  user_id: string;
  company_name: string;
  job_title: string;
  location?: string | null;
  stage: string;
  priority: string;
  salary_range?: string | null;
  match_score?: number | null;
  applied_date?: string | null;
  is_archived: boolean;
  created_at: string;
}

export interface JobApplicationCreatePayload {
  company_name: string;
  job_title: string;
  job_description_id?: string | null;
  tailored_resume_id?: string | null;
  match_evaluation_id?: string | null;
  location?: string | null;
  stage?: string;
  priority?: string;
  salary_range?: string | null;
  job_url?: string | null;
  applied_date?: string | null;
  deadline?: string | null;
  notes?: string | null;
}

export interface JobApplicationUpdatePayload {
  company_name?: string;
  job_title?: string;
  job_description_id?: string | null;
  tailored_resume_id?: string | null;
  match_evaluation_id?: string | null;
  location?: string | null;
  stage?: string;
  priority?: string;
  salary_range?: string | null;
  job_url?: string | null;
  applied_date?: string | null;
  deadline?: string | null;
  notes?: string | null;
  is_archived?: boolean;
}

export interface OpportunityComparisonItem {
  application_id: string;
  company_name: string;
  job_title: string;
  location?: string | null;
  stage: string;
  priority: string;
  salary_range?: string | null;
  overall_match_score?: number | null;
  skill_match_score?: number | null;
  experience_score?: number | null;
  top_demonstrated_skills: string[];
  critical_missing_skills: string[];
}

export interface OpportunityComparisonResponse {
  opportunities: OpportunityComparisonItem[];
  comparison_summary: string;
}

export async function listApplications(
  stage?: string,
  search?: string
): Promise<JobApplicationSummary[]> {
  const params = new URLSearchParams();
  if (stage && stage !== "ALL") params.append("stage", stage);
  if (search) params.append("search", search);

  const query = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${API_BASE}/applications${query}`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    if (res.status === 401) {
      handle401();
      throw new Error("Authentication required. Please sign in.");
    }
    const err = await parseApiError(res, "Failed to load job applications.");
    throw new Error(err);
  }
  return await res.json();
}

export async function getApplication(id: string): Promise<JobApplication> {
  const res = await fetch(`${API_BASE}/applications/${id}`, {
    headers: {
      ...authHeader(),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error("Failed to load application details.");
  }
  return await res.json();
}

export async function createApplication(
  data: JobApplicationCreatePayload
): Promise<JobApplication> {
  const res = await fetch(`${API_BASE}/applications`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create application.");
  }
  return await res.json();
}

export async function updateApplication(
  id: string,
  data: JobApplicationUpdatePayload
): Promise<JobApplication> {
  const res = await fetch(`${API_BASE}/applications/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update application.");
  }
  return await res.json();
}

export async function updateApplicationStage(
  id: string,
  stage: string,
  note?: string
): Promise<JobApplication> {
  const res = await fetch(`${API_BASE}/applications/${id}/stage`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ stage, note }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update application stage.");
  }
  return await res.json();
}

export async function deleteApplication(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/applications/${id}`, {
    method: "DELETE",
    headers: {
      ...authHeader(),
    },
  });
  if (!res.ok) {
    throw new Error("Failed to delete application.");
  }
}

export async function compareOpportunities(
  applicationIds: string[]
): Promise<OpportunityComparisonResponse> {
  const res = await fetch(`${API_BASE}/applications/compare`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeader(),
    },
    body: JSON.stringify({ application_ids: applicationIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to compare opportunities.");
  }
  return await res.json();
}
