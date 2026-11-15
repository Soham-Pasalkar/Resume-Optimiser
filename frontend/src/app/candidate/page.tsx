"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  UserCheck,
  RefreshCw,
  Plus,
  ShieldCheck,
  CheckCircle,
  XCircle,
  Trash2,
  Tag,
  BookOpen,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import {
  buildCandidateProfile,
  getCandidateProfile,
  verifyCandidateSkill,
  addCustomSkill,
  deleteCandidateSkill,
  CandidateSkill,
} from "@/lib/api";

export default function CandidateProfilePage() {
  const [skills, setSkills] = useState<CandidateSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // New Skill Modal/Form
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSkillName, setNewSkillName] = useState("");
  const [newSkillCategory, setNewSkillCategory] = useState("Programming Languages");
  const [newSkillProficiency, setNewSkillProficiency] = useState("proficient");
  const [newSkillEvidence, setNewSkillEvidence] = useState("");
  const [submittingSkill, setSubmittingSkill] = useState(false);

  // Filter
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    try {
      setLoading(true);
      const data = await getCandidateProfile();
      setSkills(data);
    } catch (err: any) {
      setError(err.message || "Failed to load candidate profile");
    } finally {
      setLoading(false);
    }
  }

  async function handleSyncFromResume() {
    try {
      setSyncing(true);
      setError(null);
      const updated = await buildCandidateProfile();
      setSkills(updated);
      if (updated.length === 0) {
        setError("No skills could be extracted yet. Please upload a resume on the Ingestion page first.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to sync candidate profile from resume");
    } finally {
      setSyncing(false);
    }
  }

  async function handleToggleVerify(skill: CandidateSkill) {
    try {
      const updated = await verifyCandidateSkill(skill.id, !skill.is_user_verified);
      setSkills((prev) => prev.map((s) => (s.id === skill.id ? updated : s)));
    } catch (err: any) {
      setError(err.message || "Failed to toggle skill verification");
    }
  }

  async function handleDeleteSkill(id: string) {
    if (!confirm("Are you sure you want to remove this skill from your master profile?")) return;
    try {
      await deleteCandidateSkill(id);
      setSkills((prev) => prev.filter((s) => s.id !== id));
    } catch (err: any) {
      setError(err.message || "Failed to delete skill");
    }
  }

  async function handleAddSkill(e: React.FormEvent) {
    e.preventDefault();
    if (!newSkillName.trim()) return;

    try {
      setSubmittingSkill(true);
      const added = await addCustomSkill({
        skill_name: newSkillName.trim(),
        category: newSkillCategory,
        proficiency_level: newSkillProficiency,
        evidence_text: newSkillEvidence.trim() || undefined,
      });

      setSkills((prev) => {
        const filtered = prev.filter((s) => s.id !== added.id);
        return [...filtered, added].sort((a, b) => a.normalized_name.localeCompare(b.normalized_name));
      });

      setNewSkillName("");
      setNewSkillEvidence("");
      setShowAddForm(false);
    } catch (err: any) {
      setError(err.message || "Failed to add skill");
    } finally {
      setSubmittingSkill(false);
    }
  }

  const categories = Array.from(new Set(skills.map((s) => s.category))).sort();
  const verifiedCount = skills.filter((s) => s.is_user_verified).length;
  const filteredSkills =
    selectedCategory === "all" ? skills : skills.filter((s) => s.category === selectedCategory);

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-soft-text flex items-center gap-2">
            <UserCheck className="w-6 h-6 text-soft-blue" />
            Master Candidate Profile
          </h1>
          <p className="text-sm text-soft-muted mt-1">
            Factual, evidence-grounded competencies extracted directly from your uploaded resume documents.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn-soft px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-4 h-4 text-soft-blue" />
            Add Skill
          </button>
          <button
            onClick={handleSyncFromResume}
            disabled={syncing}
            className="btn-primary px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${syncing ? "animate-spin" : ""}`} />
            {syncing ? "Syncing..." : "Sync from Resume"}
          </button>
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

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="surface p-5 rounded-2xl space-y-1">
          <p className="text-xs font-semibold text-soft-muted uppercase">Extracted Competencies</p>
          <p className="text-2xl font-bold text-soft-text">{skills.length}</p>
          <p className="text-[11px] text-soft-muted">Anchored to resume bullet evidence</p>
        </div>

        <div className="surface p-5 rounded-2xl space-y-1">
          <p className="text-xs font-semibold text-soft-muted uppercase">Verified by Candidate</p>
          <div className="flex items-center gap-2">
            <p className="text-2xl font-bold text-soft-green-text">{verifiedCount}</p>
            <ShieldCheck className="w-5 h-5 text-soft-green" />
          </div>
          <p className="text-[11px] text-soft-muted">
            {skills.length > 0 ? `${Math.round((verifiedCount / skills.length) * 100)}% verified` : "0%"}
          </p>
        </div>

        <div className="surface p-5 rounded-2xl space-y-1">
          <p className="text-xs font-semibold text-soft-muted uppercase">Taxonomy Domains</p>
          <p className="text-2xl font-bold text-soft-blue">{categories.length}</p>
          <p className="text-[11px] text-soft-muted">Languages, cloud, databases & tools</p>
        </div>
      </div>

      {/* Add Custom Skill Expandable Box */}
      {showAddForm && (
        <div className="surface p-6 rounded-2xl space-y-4 border border-blue-200">
          <h2 className="text-sm font-bold text-soft-text flex items-center gap-2">
            <Plus className="w-4 h-4 text-soft-blue" />
            Add Custom Verified Competency
          </h2>

          <form onSubmit={handleAddSkill} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                Skill Name *
              </label>
              <input
                type="text"
                placeholder="e.g. PyTorch, Rust, Kubernetes"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                className="w-full text-xs rounded-xl well border border-white/60 px-3.5 py-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                Category
              </label>
              <select
                value={newSkillCategory}
                onChange={(e) => setNewSkillCategory(e.target.value)}
                className="w-full text-xs rounded-xl well border border-white/60 px-3.5 py-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
              >
                <option value="Programming Languages">Programming Languages</option>
                <option value="Frameworks & Libraries">Frameworks & Libraries</option>
                <option value="Databases & Storage">Databases & Storage</option>
                <option value="Cloud & Infrastructure">Cloud & Infrastructure</option>
                <option value="AI & Machine Learning">AI & Machine Learning</option>
                <option value="Architecture & Methodologies">Architecture & Methodologies</option>
                <option value="Tools & Systems">Tools & Systems</option>
                <option value="Other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                Proficiency
              </label>
              <select
                value={newSkillProficiency}
                onChange={(e) => setNewSkillProficiency(e.target.value)}
                className="w-full text-xs rounded-xl well border border-white/60 px-3.5 py-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
              >
                <option value="proficient">Proficient</option>
                <option value="advanced">Advanced</option>
                <option value="expert">Expert</option>
                <option value="familiar">Familiar</option>
              </select>
            </div>

            <div className="md:col-span-3">
              <label className="block text-xs font-semibold text-soft-muted uppercase mb-1">
                Evidence or Practical Demonstration (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Built high-throughput data processing pipeline with Rust."
                value={newSkillEvidence}
                onChange={(e) => setNewSkillEvidence(e.target.value)}
                className="w-full text-xs rounded-xl well border border-white/60 px-3.5 py-2.5 text-soft-text focus:outline-none focus:ring-2 focus:ring-soft-blue"
              />
            </div>

            <div className="md:col-span-3 flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="btn-soft px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submittingSkill}
                className="btn-primary px-5 py-2 rounded-xl text-xs font-semibold cursor-pointer disabled:opacity-50"
              >
                {submittingSkill ? "Saving..." : "Save Competency"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Category Pills Filter */}
      {categories.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <button
            onClick={() => setSelectedCategory("all")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              selectedCategory === "all"
                ? "well text-soft-blue border border-soft-blue"
                : "surface text-soft-muted hover:text-soft-text"
            }`}
          >
            All Categories ({skills.length})
          </button>
          {categories.map((cat) => {
            const count = skills.filter((s) => s.category === cat).length;
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  selectedCategory === cat
                    ? "well text-soft-blue border border-soft-blue"
                    : "surface text-soft-muted hover:text-soft-text"
                }`}
              >
                {cat} ({count})
              </button>
            );
          })}
        </div>
      )}

      {/* Skills Grid */}
      {loading ? (
        <div className="surface p-12 text-center text-xs text-soft-muted rounded-2xl">
          Loading candidate profile...
        </div>
      ) : skills.length === 0 ? (
        <div className="surface p-12 text-center rounded-2xl space-y-4">
          <Sparkles className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="text-sm font-bold text-soft-text">No Skills In Profile Yet</h3>
          <p className="text-xs text-soft-muted max-w-md mx-auto">
            Upload your resume in the Ingestion Workspace, and CareerPilot will automatically extract evidence-grounded skills into your Master Candidate Profile.
          </p>
          <div className="pt-2">
            <Link
              href="/resumes"
              className="btn-primary inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl"
            >
              <span>Go to Resume Ingestion</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSkills.map((skill) => (
            <div
              key={skill.id}
              className="surface p-5 rounded-2xl flex flex-col justify-between space-y-3 border border-white/60 transition-all hover:translate-y-[-1px]"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-bold text-soft-text">
                      {skill.skill_name}
                    </h3>
                    {skill.normalized_name !== skill.skill_name && (
                      <p className="text-[11px] text-soft-blue font-medium">
                        Concept: {skill.normalized_name}
                      </p>
                    )}
                  </div>

                  <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-lg well text-soft-muted border border-white/60">
                    {skill.proficiency_level || "Proficient"}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-soft-muted bg-slate-100 px-2 py-0.5 rounded-md">
                    {skill.category}
                  </span>
                </div>

                {/* Evidence Anchor Box */}
                {skill.evidence_text ? (
                  <div className="well p-3 rounded-xl text-[11px] text-soft-text border border-white/80 space-y-1">
                    <p className="text-[10px] font-bold uppercase text-soft-muted flex items-center gap-1">
                      <BookOpen className="w-3 h-3 text-soft-blue" />
                      Resume Evidence
                    </p>
                    <p className="italic leading-relaxed text-slate-700">
                      &ldquo;{skill.evidence_text}&rdquo;
                    </p>
                  </div>
                ) : (
                  <div className="well p-2.5 rounded-xl text-[11px] text-slate-400 italic">
                    Manually added skill without resume quote
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-200/50">
                <button
                  onClick={() => handleToggleVerify(skill)}
                  className={`text-xs font-semibold px-2.5 py-1 rounded-xl transition-all cursor-pointer flex items-center gap-1.5 ${
                    skill.is_user_verified
                      ? "bg-emerald-50 text-soft-green-text border border-emerald-200"
                      : "well text-slate-500 hover:text-soft-blue"
                  }`}
                >
                  {skill.is_user_verified ? (
                    <>
                      <CheckCircle className="w-3.5 h-3.5 text-soft-green" />
                      Verified
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-3.5 h-3.5 text-slate-400" />
                      Verify Skill
                    </>
                  )}
                </button>

                <button
                  onClick={() => handleDeleteSkill(skill.id)}
                  className="p-1.5 text-slate-400 hover:text-red-600 transition-colors"
                  title="Remove skill"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
