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
} from "lucide-react";
import {
  getLLMSettings,
  listApplications,
  listInterviewPreps,
  listJobs,
  listMatches,
  listRoadmaps,
  listUserResumes,
  JobApplicationSummary,
  LLMSettings,
  MatchSummary,
  ResumeListItem,
} from "@/lib/api";

export default function DashboardHome() {
  const [resumes, setResumes] = useState<ResumeListItem[]>([]);
  const [jobsCount, setJobsCount] = useState<number>(0);
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [applications, setApplications] = useState<JobApplicationSummary[]>([]);
  const [roadmapsCount, setRoadmapsCount] = useState<number>(0);
  const [interviewsCount, setInterviewsCount] = useState<number>(0);
  const [llmSettings, setLlmSettings] = useState<LLMSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboardTelemetry() {
      try {
        setLoading(true);
        const [rList, jList, mList, aList, rdList, iList, llm] = await Promise.all([
          listUserResumes().catch(() => []),
          listJobs().catch(() => []),
          listMatches().catch(() => []),
          listApplications().catch(() => []),
          listRoadmaps().catch(() => []),
          listInterviewPreps().catch(() => []),
          getLLMSettings().catch(() => null),
        ]);
        setResumes(rList);
        setJobsCount(jList.length);
        setMatches(mList);
        setApplications(aList);
        setRoadmapsCount(rdList.length);
        setInterviewsCount(iList.length);
        setLlmSettings(llm);
      } catch {
        // Fallback gracefully
      } finally {
        setLoading(false);
      }
    }
    fetchDashboardTelemetry();
  }, []);

  const bestMatch = matches.length > 0
    ? [...matches].sort((a, b) => b.overall_score - a.overall_score)[0]
    : null;

  const activePipelineCount = applications.filter((a) => a.stage !== "REJECTED").length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Hero Welcome Banner */}
      <section className="surface p-6 sm:p-8 relative overflow-hidden rounded-2xl">
        <div className="relative z-10 max-w-3xl space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full well text-soft-blue">
              Career Intelligence Platform
            </span>
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              100% Free Local AI Engine
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-soft-text">
            Welcome to <span className="text-soft-blue">CareerPilot</span>.
          </h1>
          <p className="text-sm text-soft-muted leading-relaxed">
            Your personal, research-oriented career command center. Ingest your resume, decompose job requirements, verify competencies with factual rigor, and optimize applications with zero hallucinations.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/resumes" className="btn-primary flex items-center gap-2 text-xs py-2 px-3.5">
              <FileText className="w-4 h-4" />
              <span>Upload Master Resume</span>
            </Link>
            <Link href="/jobs" className="btn-soft flex items-center gap-2 text-xs py-2 px-3.5">
              <Target className="w-4 h-4 text-soft-blue" />
              <span>Analyze Target JD</span>
            </Link>
            <Link href="/pipeline" className="btn-soft flex items-center gap-2 text-xs py-2 px-3.5">
              <Kanban className="w-4 h-4 text-indigo-600" />
              <span>Application Pipeline</span>
            </Link>
          </div>
        </div>

        {/* Tactile Decorative Background Icon */}
        <div className="absolute -right-6 -bottom-6 opacity-10 pointer-events-none hidden sm:block">
          <Compass className="w-64 h-64 text-soft-blue" />
        </div>
      </section>

      {/* Top 4 Live Metric Cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Resumes & Master Profile */}
        <div className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-soft-muted uppercase">Master Resumes</span>
            <ShieldCheck className="w-4 h-4 text-soft-green" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-extrabold text-soft-text">
              {resumes.length} {resumes.length === 1 ? "File" : "Files"}
            </div>
            <p className="text-[11px] text-soft-muted">
              {resumes.some((r) => r.is_master) ? "Master Profile Active" : "No Master Tagged"}
            </p>
          </div>
          <div className="well p-2 rounded-lg flex items-center justify-between text-[11px]">
            <span className="text-soft-muted">Ingestion Engine:</span>
            <span className="font-semibold text-soft-green">pdfplumber + OCR</span>
          </div>
        </div>

        {/* Metric 2: Top Match Alignment */}
        <div className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-soft-muted uppercase">Top Alignment</span>
            <Target className="w-4 h-4 text-soft-blue" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-extrabold text-soft-blue">
              {bestMatch ? `${Math.round(bestMatch.overall_score)}%` : "N/A"}
            </div>
            <p className="text-[11px] text-soft-muted truncate">
              {bestMatch ? `${bestMatch.job_title}` : "Run your first match"}
            </p>
          </div>
          <div className="well p-2 rounded-lg flex items-center justify-between text-[11px]">
            <span className="text-soft-muted">Method:</span>
            <span className="font-semibold text-soft-text">Okapi BM25 + Dense</span>
          </div>
        </div>

        {/* Metric 3: Active Pipeline */}
        <div className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-soft-muted uppercase">Pipeline Tracker</span>
            <Kanban className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-extrabold text-indigo-600">
              {activePipelineCount} Active
            </div>
            <p className="text-[11px] text-soft-muted">
              {applications.length} total applications tracked
            </p>
          </div>
          <div className="well p-2 rounded-lg flex items-center justify-between text-[11px]">
            <span className="text-soft-muted">Stages:</span>
            <span className="font-semibold text-soft-text">6 Kanban Columns</span>
          </div>
        </div>

        {/* Metric 4: Local AI Daemon Status */}
        <div className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-soft-muted uppercase">Local Inference</span>
            <Cpu className="w-4 h-4 text-soft-green" />
          </div>
          <div className="space-y-1">
            <div className="text-2xl font-extrabold text-soft-green">
              {llmSettings?.daemon_status?.is_available ? "Online" : "Fallback"}
            </div>
            <p className="text-[11px] text-soft-muted truncate">
              {llmSettings?.daemon_status?.is_available
                ? llmSettings.default_model
                : "Curated Bar-Raiser Heuristics"}
            </p>
          </div>
          <div className="well p-2 rounded-lg flex items-center justify-between text-[11px]">
            <span className="text-soft-muted">Privacy:</span>
            <span className="font-semibold text-soft-green">100% Free / Zero API Cost</span>
          </div>
        </div>
      </section>

      {/* Main 2-Column Split */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column (8 cols): Top Target Opportunity or Onboarding */}
        <div className="lg:col-span-8 space-y-4">
          <div className="surface p-6 rounded-2xl space-y-5">
            <div className="flex items-center justify-between border-b pb-3 border-slate-200">
              <div>
                <h3 className="text-base font-bold text-soft-text">Current Application Focus</h3>
                <p className="text-xs text-soft-muted">
                  Highest-alignment role opportunity requiring action
                </p>
              </div>
              <Link href="/matches" className="text-xs font-bold text-soft-blue hover:underline flex items-center gap-1">
                <span>All Reports</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {bestMatch ? (
              <div className="well p-5 rounded-xl space-y-4 border-l-4 border-soft-blue">
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
                      {Math.round(bestMatch.overall_score)}% Overall Match
                    </span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-soft-muted">
                    <span>Qualification Alignment</span>
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
                    href="/optimizer"
                    className="btn-soft text-xs py-1.5 px-3 flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-soft-blue" />
                    <span>Optimize Resume (XYZ)</span>
                  </Link>
                  <Link
                    href="/learning"
                    className="btn-soft text-xs py-1.5 px-3 flex items-center gap-1.5"
                  >
                    <GraduationCap className="w-3.5 h-3.5 text-soft-green" />
                    <span>View Learning Roadmap</span>
                  </Link>
                  <Link
                    href="/interview"
                    className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5 ml-auto"
                  >
                    <span>Practice Interview</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ) : (
              <div className="well p-8 rounded-xl text-center space-y-3">
                <Target className="w-10 h-10 text-soft-blue mx-auto opacity-70" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-soft-text">Ready to run your first evaluation?</h4>
                  <p className="text-xs text-soft-muted max-w-md mx-auto">
                    Upload your resume and a target job description to generate an explainable 5-factor match score and 4-tier gap breakdown.
                  </p>
                </div>
                <Link href="/matches" className="btn-primary inline-flex items-center gap-2 text-xs py-2 px-4 mt-1">
                  <Target className="w-3.5 h-3.5" />
                  <span>Run Match Evaluation</span>
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (4 cols): Intelligence Modules Overview */}
        <div className="lg:col-span-4 space-y-4">
          <div className="surface p-6 rounded-2xl space-y-4">
            <h3 className="text-base font-bold text-soft-text border-b pb-3 border-slate-200">
              Intelligence Modules
            </h3>

            <div className="space-y-2 text-xs">
              <Link
                href="/candidate"
                className="well p-3 rounded-xl flex items-center justify-between hover:bg-white transition-colors block"
              >
                <div className="flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-soft-green" />
                  <div>
                    <span className="font-bold text-soft-text block">Master Profile</span>
                    <span className="text-[11px] text-soft-muted">Evidence-anchored skills</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-soft-muted" />
              </Link>

              <Link
                href="/optimizer"
                className="well p-3 rounded-xl flex items-center justify-between hover:bg-white transition-colors block"
              >
                <div className="flex items-center gap-2.5">
                  <Sparkles className="w-4 h-4 text-soft-blue" />
                  <div>
                    <span className="font-bold text-soft-text block">AI Resume Optimizer</span>
                    <span className="text-[11px] text-soft-muted">Google XYZ + NLI Guardrails</span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-soft-muted" />
              </Link>

              <Link
                href="/learning"
                className="well p-3 rounded-xl flex items-center justify-between hover:bg-white transition-colors block"
              >
                <div className="flex items-center gap-2.5">
                  <GraduationCap className="w-4 h-4 text-indigo-600" />
                  <div>
                    <span className="font-bold text-soft-text block">Learning Roadmaps</span>
                    <span className="text-[11px] text-soft-muted">
                      {roadmapsCount} {roadmapsCount === 1 ? "roadmap" : "roadmaps"} generated
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
                  <MessageSquareCode className="w-4 h-4 text-purple-600" />
                  <div>
                    <span className="font-bold text-soft-text block">Interview Intelligence</span>
                    <span className="text-[11px] text-soft-muted">
                      {interviewsCount} {interviewsCount === 1 ? "session" : "sessions"} active
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
                  <Kanban className="w-4 h-4 text-soft-orange" />
                  <div>
                    <span className="font-bold text-soft-text block">Pipeline Tracker</span>
                    <span className="text-[11px] text-soft-muted">
                      {applications.length} applications tracked
                    </span>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-soft-muted" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
