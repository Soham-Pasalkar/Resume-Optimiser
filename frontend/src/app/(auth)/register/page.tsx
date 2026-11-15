"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Compass, User, Mail, Lock, ArrowRight, AlertCircle, RefreshCw, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { registerUser } from "@/lib/auth";
import { useAuth } from "@/context/AuthContext";

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectPath = searchParams.get("redirect") || "/";
  const { register } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    try {
      const tokens = await registerUser(email, password, fullName);
      register(tokens);
      router.push(redirectPath);
    } catch (err: any) {
      setError(err.message || "Failed to create account. Please check your information.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4">
      <Card variant="surface" className="w-full max-w-md p-8 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-soft-lg bg-soft-blue items-center justify-center text-white shadow-md mx-auto">
            <Compass className="w-7 h-7 animate-spin-slow" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-soft-text">
            Create Your Workspace
          </h1>
          <p className="text-xs text-soft-muted">
            100% Free Career Intelligence • Powered by Local Ollama
          </p>
        </div>

        {/* Error Alert Well */}
        {error && (
          <div className="well p-3 text-soft-orange-text flex items-start gap-2 text-xs border border-orange-200">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Registration Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-soft-text uppercase tracking-wider">
              Full Name
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-soft-muted absolute left-3.5 top-3" />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Marcus Vance"
                className="input-well w-full pl-10 pr-4 py-2.5 text-sm"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-soft-text uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-soft-muted absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="marcus@example.com"
                className="input-well w-full pl-10 pr-4 py-2.5 text-sm"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-soft-text uppercase tracking-wider">
              Password (Min 8 Characters)
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-soft-muted absolute left-3.5 top-3" />
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="input-well w-full pl-10 pr-4 py-2.5 text-sm"
              />
            </div>
          </div>

          {/* Privacy Guarantee Note */}
          <div className="well p-3 text-[11px] text-soft-muted flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-soft-green-text flex-shrink-0 mt-0.5" />
            <span>
              Your profile is strictly isolated. With local Ollama, your resumes never leave your machine.
            </span>
          </div>

          <Button
            type="submit"
            variant="primary"
            disabled={loading}
            className="w-full py-3 flex items-center justify-center gap-2 mt-2"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Creating Workspace...</span>
              </>
            ) : (
              <>
                <span>Initialize My Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </form>

        {/* Footer Link */}
        <div className="text-center pt-2 border-t border-slate-200/60">
          <p className="text-xs text-soft-muted">
            Already have an account?{" "}
            <Link
              href={redirectPath !== "/" ? `/login?redirect=${encodeURIComponent(redirectPath)}` : "/login"}
              className="font-bold text-soft-blue hover:underline ml-1"
            >
              Sign in
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[85vh] flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-soft-blue" />
        </div>
      }
    >
      <RegisterForm />
    </Suspense>
  );
}
