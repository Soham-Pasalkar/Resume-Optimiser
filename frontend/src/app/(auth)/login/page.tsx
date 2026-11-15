"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Compass, Lock, Mail, ArrowRight, AlertCircle, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { loginUser } from "@/lib/auth";
import { useAuth } from "@/context/AuthContext";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectPath = searchParams.get("redirect") || "/";
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const tokens = await loginUser(email, password);
      login(tokens);
      router.push(redirectPath);
    } catch (err: any) {
      setError(err.message || "Failed to log in. Please verify your credentials.");
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
            Welcome to CareerPilot
          </h1>
          <p className="text-xs text-soft-muted">
            Sign in to access your career intelligence workspace
          </p>
        </div>

        {/* Error Alert Well */}
        {error && (
          <div className="well p-3 text-soft-orange-text flex items-start gap-2 text-xs border border-orange-200">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
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
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-soft-text uppercase tracking-wider">
                Password
              </label>
              <Link
                href="#forgot-password"
                className="text-xs text-soft-blue hover:underline"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-soft-muted absolute left-3.5 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="input-well w-full pl-10 pr-4 py-2.5 text-sm"
              />
            </div>
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
                <span>Signing In...</span>
              </>
            ) : (
              <>
                <span>Sign In to Workspace</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </form>

        {/* Footer Link */}
        <div className="text-center pt-2 border-t border-slate-200/60">
          <p className="text-xs text-soft-muted">
            Don&apos;t have an account?{" "}
            <Link
              href={redirectPath !== "/" ? `/register?redirect=${encodeURIComponent(redirectPath)}` : "/register"}
              className="font-bold text-soft-blue hover:underline"
            >
              Create free workspace
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[85vh] flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-soft-blue" />
        </div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
