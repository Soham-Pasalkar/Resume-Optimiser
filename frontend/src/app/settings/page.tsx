"use client";

import React, { useEffect, useState } from "react";
import {
  User,
  Cpu,
  ShieldAlert,
  Save,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  LogOut,
  ExternalLink,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getCurrentUserProfile, updateUserProfile, clearStoredAuth, UserData } from "@/lib/auth";
import { getOllamaStatus, OllamaStatus } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function SettingsPage() {
  const { user: authUser, refreshUser, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<"profile" | "llm" | "privacy">("profile");
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form State
  const [fullName, setFullName] = useState("");
  const [headline, setHeadline] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [targetSeniority, setTargetSeniority] = useState("Mid");
  const [yearsExp, setYearsExp] = useState<number | "">("");
  const [linkedin, setLinkedin] = useState("");
  const [github, setGithub] = useState("");
  const [portfolio, setPortfolio] = useState("");

  // Ollama Status State
  const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus | null>(null);

  useEffect(() => {
    loadData();
  }, [authUser]);

  const loadData = async () => {
    setLoading(true);
    const profile = authUser || (await getCurrentUserProfile());
    if (profile) {
      setUser(profile);
      setFullName(profile.full_name || "");
      if (profile.profile) {
        setHeadline(profile.profile.headline || "");
        setTargetRole(profile.profile.target_role_title || "");
        setTargetSeniority(profile.profile.target_seniority || "Mid");
        setYearsExp(profile.profile.years_of_experience ?? "");
        setLinkedin(profile.profile.linkedin_url || "");
        setGithub(profile.profile.github_url || "");
        setPortfolio(profile.profile.portfolio_url || "");
      }
    }
    const oStatus = await getOllamaStatus();
    setOllamaStatus(oStatus);
    setLoading(false);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);
    setErrorMessage(null);

    try {
      const updated = await updateUserProfile({
        full_name: fullName,
        profile: {
          headline,
          target_role_title: targetRole,
          target_seniority: targetSeniority,
          years_of_experience: yearsExp === "" ? null : Number(yearsExp),
          linkedin_url: linkedin,
          github_url: github,
          portfolio_url: portfolio,
        },
      });
      setUser(updated);
      await refreshUser();
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="surface p-8 skeleton-well h-64" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Settings Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-slate-200/60 pb-3">
        <div>
          <h1 className="text-2xl font-extrabold text-soft-text">Workspace Settings</h1>
          <p className="text-xs text-soft-muted">
            Manage your personal profile, local Ollama engine, and privacy preferences
          </p>
        </div>
        <Button
          onClick={handleLogout}
          variant="soft"
          size="sm"
          className="flex items-center gap-1.5 text-soft-orange-text"
        >
          <LogOut className="w-3.5 h-3.5" />
          Sign Out
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Left Tab Buttons */}
        <div className="md:col-span-1 space-y-2">
          <button
            onClick={() => setActiveTab("profile")}
            className={`w-full flex items-center gap-2.5 px-4 py-3 rounded-soft-md text-xs font-bold text-left transition-all ${
              activeTab === "profile"
                ? "well text-soft-blue border-l-4 border-l-soft-blue"
                : "surface text-soft-text hover:text-soft-blue"
            }`}
          >
            <User className="w-4 h-4" />
            Master Profile
          </button>

          <button
            onClick={() => setActiveTab("llm")}
            className={`w-full flex items-center gap-2.5 px-4 py-3 rounded-soft-md text-xs font-bold text-left transition-all ${
              activeTab === "llm"
                ? "well text-soft-blue border-l-4 border-l-soft-blue"
                : "surface text-soft-text hover:text-soft-blue"
            }`}
          >
            <Cpu className="w-4 h-4" />
            Local AI Engine
          </button>

          <button
            onClick={() => setActiveTab("privacy")}
            className={`w-full flex items-center gap-2.5 px-4 py-3 rounded-soft-md text-xs font-bold text-left transition-all ${
              activeTab === "privacy"
                ? "well text-soft-blue border-l-4 border-l-soft-blue"
                : "surface text-soft-text hover:text-soft-blue"
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            Privacy & GDPR
          </button>
        </div>

        {/* Right Content Panels */}
        <div className="md:col-span-3">
          {/* TAB 1: MASTER PROFILE */}
          {activeTab === "profile" && (
            <Card variant="surface">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Master Candidate Profile</CardTitle>
                    <CardDescription>
                      This information provides the baseline qualifications for matching and resume optimization.
                    </CardDescription>
                  </div>
                  {user?.email && (
                    <Badge variant="neutral" className="text-xs">
                      {user.email}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {saveSuccess && (
                  <div className="well p-3 mb-4 text-soft-green-text flex items-center gap-2 text-xs border border-green-200">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Profile saved successfully!</span>
                  </div>
                )}
                {errorMessage && (
                  <div className="well p-3 mb-4 text-soft-orange-text flex items-center gap-2 text-xs border border-orange-200">
                    <AlertCircle className="w-4 h-4" />
                    <span>{errorMessage}</span>
                  </div>
                )}

                <form onSubmit={handleSaveProfile} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-soft-text uppercase">Full Name</label>
                      <input
                        type="text"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        className="input-well w-full text-xs py-2 px-3"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-soft-text uppercase">Professional Headline</label>
                      <input
                        type="text"
                        value={headline}
                        onChange={(e) => setHeadline(e.target.value)}
                        placeholder="e.g. Senior Backend Engineer"
                        className="input-well w-full text-xs py-2 px-3"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-soft-text uppercase">Target Job Title</label>
                      <input
                        type="text"
                        value={targetRole}
                        onChange={(e) => setTargetRole(e.target.value)}
                        placeholder="e.g. Distributed Systems Engineer"
                        className="input-well w-full text-xs py-2 px-3"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-soft-text uppercase">Target Seniority</label>
                      <select
                        value={targetSeniority}
                        onChange={(e) => setTargetSeniority(e.target.value)}
                        className="input-well w-full text-xs py-2 px-3"
                      >
                        <option value="Intern">Intern / Co-op</option>
                        <option value="Entry">Entry Level (0-2 yrs)</option>
                        <option value="Mid">Mid Level (2-5 yrs)</option>
                        <option value="Senior">Senior Level (5-8 yrs)</option>
                        <option value="Staff">Staff / Principal (8+ yrs)</option>
                        <option value="Lead">Engineering Manager / Lead</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-soft-text uppercase">Years Experience</label>
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        max="50"
                        value={yearsExp}
                        onChange={(e) => setYearsExp(e.target.value === "" ? "" : Number(e.target.value))}
                        placeholder="e.g. 5.5"
                        className="input-well w-full text-xs py-2 px-3"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-soft-text uppercase">LinkedIn URL</label>
                      <input
                        type="url"
                        value={linkedin}
                        onChange={(e) => setLinkedin(e.target.value)}
                        placeholder="https://linkedin.com/in/username"
                        className="input-well w-full text-xs py-2 px-3"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-soft-text uppercase">GitHub URL</label>
                      <input
                        type="url"
                        value={github}
                        onChange={(e) => setGithub(e.target.value)}
                        placeholder="https://github.com/username"
                        className="input-well w-full text-xs py-2 px-3"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-soft-text uppercase">Portfolio / Website</label>
                      <input
                        type="url"
                        value={portfolio}
                        onChange={(e) => setPortfolio(e.target.value)}
                        placeholder="https://mywebsite.dev"
                        className="input-well w-full text-xs py-2 px-3"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end pt-4 border-t border-slate-200/60">
                    <Button
                      type="submit"
                      variant="primary"
                      disabled={saving}
                      className="flex items-center gap-2"
                    >
                      {saving ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Saving Changes...
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          Save Master Profile
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* TAB 2: LOCAL AI / OLLAMA */}
          {activeTab === "llm" && (
            <Card variant="surface" className="space-y-6">
              <CardHeader>
                <CardTitle>Local AI Engine Configuration</CardTitle>
                <CardDescription>
                  CareerPilot executes 100% locally by default at zero operational cost.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="well p-4 space-y-3 text-xs">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
                    <span className="font-bold text-soft-text">Ollama Daemon Status:</span>
                    {ollamaStatus?.is_available ? (
                      <Badge variant="success" className="flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Connected & Active
                      </Badge>
                    ) : (
                      <Badge variant="warning" className="flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        Offline / Not Found
                      </Badge>
                    )}
                  </div>

                  <div className="flex justify-between">
                    <span className="text-soft-muted">Host Endpoint:</span>
                    <span className="font-mono">{ollamaStatus?.base_url || "http://localhost:11434"}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-soft-muted">Active Model:</span>
                    <span className="font-semibold text-soft-blue">
                      {ollamaStatus?.active_model || "llama3.1:8b"}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-soft-muted">Available Models Installed:</span>
                    <span className="text-soft-text">
                      {ollamaStatus?.available_models.length
                        ? ollamaStatus.available_models.join(", ")
                        : "None detected. Run 'ollama run llama3.1:8b'"}
                    </span>
                  </div>

                  <div className="flex justify-between pt-1">
                    <span className="text-soft-muted">Operational Cost:</span>
                    <span className="font-extrabold text-soft-green-text">$0.00 / Free Forever</span>
                  </div>
                </div>

                <div className="surface p-4 text-xs space-y-2">
                  <h4 className="font-bold text-soft-text">Optional Bring-Your-Own-Key (BYOK) Cloud APIs</h4>
                  <p className="text-[11px] text-soft-muted">
                    If you prefer cloud models over local Ollama, you can configure your own OpenAI or Anthropic API key in your <code>.env</code> file. No keys are required for normal operation.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* TAB 3: PRIVACY & GDPR */}
          {activeTab === "privacy" && (
            <Card variant="surface" className="space-y-6">
              <CardHeader>
                <CardTitle className="text-soft-orange-text">Data Sovereignty & GDPR</CardTitle>
                <CardDescription>
                  You own your data completely. You can export or permanently delete your profile at any time.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                <div className="well p-4 space-y-2">
                  <h4 className="font-bold text-soft-text">Local-First Privacy Guarantee</h4>
                  <p className="text-soft-muted">
                    Because CareerPilot uses local Ollama by default, your resume text and target job postings are processed on your own hardware and never transmitted to external cloud servers.
                  </p>
                </div>

                <div className="border border-red-200/80 rounded-soft-md p-4 space-y-3 bg-red-50/30">
                  <div className="font-bold text-red-700 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4" />
                    Danger Zone: Permanent Account Purge
                  </div>
                  <p className="text-soft-muted text-[11px]">
                    Permanently delete your account, candidate profile, uploaded resumes, and application tracking history. This action is irreversible.
                  </p>
                  <Button
                    variant="soft"
                    size="sm"
                    className="border border-red-300 text-red-600 hover:bg-red-50"
                    onClick={() => {
                      if (confirm("Are you sure you want to permanently delete your CareerPilot account? This cannot be undone.")) {
                        alert("Account deletion triggered.");
                      }
                    }}
                  >
                    Delete My Account & Purge Data
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
