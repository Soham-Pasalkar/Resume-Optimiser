"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Compass,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  FileText,
  Target,
  Zap,
  BookOpen,
  Briefcase,
  Layers,
  GraduationCap,
  MessageSquareCode,
  Kanban,
  ExternalLink,
  ChevronRight,
  Activity,
  Cpu,
  UserCheck,
  Award,
  FileCheck,
} from "lucide-react";
import {
  getCandidateProfile,
  getLLMSettings,
  listApplications,
  listInterviewPreps,
  listJobs,
  listMatches,
  listRoadmaps,
  listTailoredResumes,
  listUserResumes,
  CandidateSkill,
  JobApplicationSummary,
  LLMSettings,
  MatchSummary,
  ResumeListItem,
  TailoredResumeSummary,
} from "@/lib/api";

export default function DashboardHome() {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [jobsCount, setJobsCount] = useState<number>(0);
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [applications, setApplications] = useState<JobApplicationSummary[]>([]);
  const [skills, setSkills] = useState<CandidateSkill[]>([]);
  const [tailoredResumes, setTailoredResumes] = useState<TailoredResumeSummary[]>([]);
  const [roadmapsCount, setRoadmapsCount] = useState<number>(0);
  const [interviewsCount, setInterviewsCount] = useState<number>(0);
  const [llmSettings, setLlmSettings] = useState<LLMSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboardTelemetry() {
      try {
        setLoading(true);
        const [rList, jList, mList, aList, rdList, iList, sList, tList, llm] = await Promise.all([
          listUserResumes().catch(() => []),
          listJobs().catch(() => []),
          listMatches().catch(() => []),
          listApplications().catch(() => []),
          listRoadmaps().catch(() => []),
          listInterviewPreps().catch(() => []),
          getCandidateProfile().catch(() => []),
          listTailoredResumes().catch(() => []),
          getLLMSettings().catch(() => null),
        ]);
        setResumes(rList);
        setJobsCount(jList.length);
        setMatches(mList);
        setApplications(aList);
        setRoadmapsCount(rdList.length);
        setInterviewsCount(iList.length);
        setSkills(sList);
        setTailoredResumes(tList);
        setLlmSettings(llm);
      } catch {
        // Fallback gracefully
      } finally {
        setLoading(false);
      }
    }
    fetchDashboardTelemetry();
  }, []);

  const bestMatch =
    matches.length > 0
      ? [...matches].sort((a, b) => b.overall_score - a.overall_score)[0]
      : null;

  const verifiedSkillsCount = skills.filter((s) => s.is_user_verified).length;
  const activePipelineCount = applications.filter((a) => a.stage !== "REJECTED" && a.stage !== "WITHDRAWN").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      {/* Hero Welcome Banner */}
      <section className="surface p-6 sm:p-8 relative overflow-hidden rounded-2xl border border-slate-200/60 shadow-sm">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full well text-soft-blue">
              CareerPilot 2.0
            </span>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              100% Free Local AI Engine
            </span>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
              Factual Integrity Guaranteed
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-soft-text">
            Analyze a job. Understand your gaps. <span className="text-soft-blue">Build a better resume.</span>
          </h1>
          <p className="text-xs sm:text-sm text-soft-muted leading-relaxed">
            CareerPilot bridges the gap between target opportunities and verified candidate qualifications. Generate ATS-optimized, evidence-grounded resumes without hallucinated claims or fabricated metrics.
          </p>

          {/* Primary & Secondary Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              href="/jobs"
              className="btn-primary flex items-center gap-2 text-xs py-2.5 px-4 rounded-xl shadow-md"
            >
              <Target className="w-4 h-4" />
              <span>Analyze a New Job</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
            <Link
              href="/candidate"
              className="btn-soft flex items-center gap-2 text-xs py-2.5 px-4 rounded-xl"
            >
              <UserCheck className="w-4 h-4 text-soft-blue" />
              <span>Update Career Profile</span>
            </Link>
            <Link
              href="/optimizer"
              className="btn-soft flex items-center gap-2 text-xs py-2.5 px-4 rounded-xl"
            >
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span>Resume Studio</span>
            </Link>
            <Link
              href="/learning"
              className="btn-soft flex items-center gap-2 text-xs py-2.5 px-4 rounded-xl"
            >
              <GraduationCap className="w-4 h-4 text-emerald-600" />
              <span>Review Learning Plans</span>
            </Link>
          </div>
        </div>

        {/* Decorative Compass Icon */}
        <div className="absolute -right-6 -bottom-6 opacity-10 pointer-events-none hidden sm:block">
          <Compass className="w-64 h-64 text-soft-blue" />
        </div>
      </section>

      {/* Guided 5-Step Core Workflow Banner */}
      <section className="surface p-4 sm:p-5 rounded-2xl border border-slate-200/60 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-extrabold uppercase tracking-wider text-soft-muted">
            Core Workflow Journey
          </span>
          <span className="text-[11px] text-soft-blue font-semibold">Step-by-step intelligence</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs">
          <Link
            href="/candidate"
            className="well p-3 rounded-xl border border-slate-200/60 hover:border-soft-blue transition-colors group block"
          >
            <div className="flex items-center gap-2 text-soft-blue font-bold mb-1">
              <span className="w-5 h-5 rounded-full bg-soft-blue text-white flex items-center justify-center text-[10px]">1</span>
              <span>Career Profile</span>
            </div>
            <p className="text-[11px] text-soft-muted">
              {skills.length} skills ({verifiedSkillsCount} verified)
            </p>
          </Link>

          <Link
            href="/jobs"
            className="well p-3 rounded-xl border border-slate-200/60 hover:border-soft-blue transition-colors group block"
          >
            <div className="flex items-center gap-2 text-soft-blue font-bold mb-1">
              <span className="w-5 h-5 rounded-full bg-soft-blue text-white flex items-center justify-center text-[10px]">2</span>
              <span>Analyze Job</span>
            </div>
            <p className="text-[11px] text-soft-muted">
              {jobsCount} {jobsCount === 1 ? "opportunity" : "opportunities"} tracked
            </p>
          </Link>

          <Link
            href="/matches"
            className="well p-3 rounded-xl border border-slate-200/60 hover:border-soft-blue transition-colors group block"
          >
            <div className="flex items-center gap-2 text-soft-blue font-bold mb-1">
              <span className="w-5 h-5 rounded-full bg-soft-blue text-white flex items-center justify-center text-[10px]">3</span>
              <span>Gap Analysis</span>
            </div>
            <p className="text-[11px] text-soft-muted">
              {matches.length} {matches.length === 1 ? "evaluation" : "evaluations"} run
            </p>
          </Link>

          <Link
            href="/optimizer"
            className="well p-3 rounded-xl border border-slate-200/60 hover:border-soft-blue transition-colors group block"
          >
            <div className="flex items-center gap-2 text-soft-blue font-bold mb-1">
              <span className="w-5 h-5 rounded-full bg-soft-blue text-white flex items-center justify-center text-[10px]">4</span>
              <span>Resume Studio</span>
            </div>
            <p className="text-[11px] text-soft-muted">
              {tailoredResumes.length} {tailoredResumes.length === 1 ? "tailored version" : "tailored versions"}
            </p>
          </Link>

          <Link
            href="/optimizer"
            className="well p-3 rounded-xl border border-slate-200/60 hover:border-soft-blue transition-colors group block"
          >
            <div className="flex items-center gap-2 text-soft-blue font-bold mb-1">
              <span className="w-5 h-5 rounded-full bg-soft-blue text-white flex items-center justify-center text-[10px]">5</span>
              <span>Export ATS</span>
            </div>
            <p className="text-[11px] text-soft-muted">
              Download clean PDF / DOCX
            </p>
          </Link>
        </div>
      </section>

      {/* Top 4 Live Metric Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Career Profile Competencies */}
        <div className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3 border border-slate-200/60">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-soft-muted uppercase">Career Profile</span>
            <ShieldCheck className="w-4 h-4 text-soft-green" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-extrabold text-soft-text">
              {skills.length} <span className="text-xs font-normal text-soft-muted">Skills</span>
            </div>
            <p className="text-[11px] text-soft-muted">
              {verifiedSkillsCount} candidate-verified • {resumes.length} {resumes.length === 1 ? "source resume" : "source resumes"}
            </p>
          </div>
          <Link
            href="/candidate"
            className="well p-2 rounded-lg flex items-center justify-between text-[11px] hover:text-soft-blue transition-colors"
          >
            <span>View Competencies</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Metric 2: Target Opportunities */}
        <div className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3 border border-slate-200/60">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-soft-muted uppercase">Target Jobs</span>
            <Target className="w-4 h-4 text-soft-blue" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-extrabold text-soft-text">
              {jobsCount} <span className="text-xs font-normal text-soft-muted">Tracked</span>
            </div>
            <p className="text-[11px] text-soft-muted">
              Decomposed into mandatory & preferred requirements
            </p>
          </div>
          <Link
            href="/jobs"
            className="well p-2 rounded-lg flex items-center justify-between text-[11px] hover:text-soft-blue transition-colors"
          >
            <span>Analyze Opportunities</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Metric 3: Top Match Alignment */}
        <div className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3 border border-slate-200/60">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-soft-muted uppercase">Top Alignment</span>
            <Award className="w-4 h-4 text-amber-500" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-extrabold text-soft-blue">
              {bestMatch ? `${Math.round(bestMatch.overall_score)}%` : "N/A"}
            </div>
            <p className="text-[11px] text-soft-muted truncate">
              {bestMatch ? `${bestMatch.job_title}` : "Run your first match"}
            </p>
          </div>
          <Link
            href="/matches"
            className="well p-2 rounded-lg flex items-center justify-between text-[11px] hover:text-soft-blue transition-colors"
          >
            <span>Inspect Gap Analysis</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Metric 4: Resume Studio Drafts */}
        <div className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3 border border-slate-200/60">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-soft-muted uppercase">Resume Studio</span>
            <FileCheck className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-extrabold text-soft-text">
              {tailoredResumes.length} <span className="text-xs font-normal text-soft-muted">Tailored</span>
            </div>
            <p className="text-[11px] text-soft-muted">
              ATS-verified documents with Google XYZ diffs
            </p>
          </div>
          <Link
            href="/optimizer"
            className="well p-2 rounded-lg flex items-center justify-between text-[11px] hover:text-soft-blue transition-colors"
          >
            <span>Open Studio</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </section>

      {/* Main Content 2-Column Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Top Target Opportunity & Gap Overview */}
        <div className="lg:col-span-8 space-y-6">
          <div className="surface p-6 rounded-2xl border border-slate-200/60 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200/60 pb-3">
              <div>
                <h3 className="text-base font-bold text-soft-text">Recent Gap Analysis</h3>
                <p className="text-xs text-soft-muted">
                  Direct evaluation of your master profile against target opportunity requirements
                </p>
              </div>
              <Link href="/matches" className="text-xs text-soft-blue font-semibold hover:underline">
                View All Matches ({matches.length})
              </Link>
            </div>

            {loading ? (
              <div className="p-8 text-center text-xs text-soft-muted">Loading telemetry...</div>
            ) : bestMatch ? (
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-base text-soft-text">
                        {bestMatch.job_title}
                      </span>
                      {bestMatch.company_name && (
                        <span className="text-xs text-soft-muted font-semibold">
                          @ {bestMatch.company_name}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-soft-muted mt-0.5">
                      Evaluated on {new Date(bestMatch.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
                      {Math.round(bestMatch.overall_score)}% Alignment
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-soft-muted">
                    <span>Evidence-Grounded Qualification Alignment</span>
                    <span className="font-bold text-soft-text">
                      {Math.round(bestMatch.overall_score)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-soft-blue h-full rounded-full transition-all"
                      style={{ width: `${Math.min(100, Math.round(bestMatch.overall_score))}%` }}
                    />
                  </div>
                </div>

                {/* Quick Actions Row */}
                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-200/60">
                  <Link
                    href={`/optimizer?match_id=${bestMatch.id}&jd_id=${bestMatch.jd_id}&resume_id=${bestMatch.resume_id}`}
                    className="btn-primary text-xs py-2 px-3.5 flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Open in Resume Studio</span>
                  </Link>
                  <Link
                    href={`/learning?match_id=${bestMatch.id}`}
                    className="btn-soft text-xs py-2 px-3.5 flex items-center gap-1.5"
                  >
                    <GraduationCap className="w-3.5 h-3.5 text-soft-green" />
                    <span>View Learning Plan</span>
                  </Link>
                  <Link
                    href={`/interview?match_id=${bestMatch.id}`}
                    className="btn-soft text-xs py-2 px-3.5 flex items-center gap-1.5 ml-auto"
                  >
                    <MessageSquareCode className="w-3.5 h-3.5 text-soft-blue" />
                    <span>Practice Interview</span>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="well p-8 rounded-xl text-center space-y-3">
                <Target className="w-10 h-10 text-soft-blue mx-auto opacity-70" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-soft-text">No evaluations yet</h4>
                  <p className="text-xs text-soft-muted max-w-md mx-auto">
                    Analyze a target job description and compare it against your career profile to identify exact gaps.
                  </p>
                </div>
                <Link href="/jobs" className="btn-primary inline-flex items-center gap-2 text-xs py-2 px-4 mt-1">
                  <Target className="w-3.5 h-3.5" />
                  <span>Analyze Target Job</span>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (4 cols): Quick Status & Career Development */}
        <div className="lg:col-span-4 space-y-4">
          <div className="surface p-6 rounded-2xl border border-slate-200/60 space-y-4">
            <h3 className="text-base font-bold text-soft-text border-b pb-3 border-slate-200/60">
              Career Development
            </h3>

            <div className="space-y-2 text-xs">
              <Link
                href="/learning"
                className="well p-3 rounded-xl flex items-center justify-between hover:bg-white transition-colors block"
              >
                <div className="flex items-center gap-2.5">
                  <GraduationCap className="w-4 h-4 text-emerald-600" />
                  <div>
                    <span className="font-bold text-soft-text block">Learning & Projects</span>
                    <span className="text-[11px] text-soft-muted">
                      {roadmapsCount} active {roadmapsCount === 1 ? "roadmap" : "roadmaps"}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-soft-muted" />
              </Link>

              <Link
                href="/interview"
                className="well p-3 rounded-xl flex items-center justify-between hover:bg-white transition-colors block"
              >
                <div className="flex items-center gap-2.5">
                  <MessageSquareCode className="w-4 h-4 text-soft-blue" />
                  <div>
                    <span className="font-bold text-soft-text block">Interview Preparation</span>
                    <span className="text-[11px] text-soft-muted">
                      {interviewsCount} practice {interviewsCount === 1 ? "session" : "sessions"}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-soft-muted" />
              </Link>

              <Link
                href="/pipeline"
                className="well p-3 rounded-xl flex items-center justify-between hover:bg-white transition-colors block"
              >
                <div className="flex items-center gap-2.5">
                  <Kanban className="w-4 h-4 text-indigo-600" />
                  <div>
                    <span className="font-bold text-soft-text block">Application Tracker</span>
                    <span className="text-[11px] text-soft-muted">
                      {activePipelineCount} active {activePipelineCount === 1 ? "application" : "applications"}
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-soft-muted" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
