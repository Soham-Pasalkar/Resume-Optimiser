"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Lock, LogIn, UserPlus, RefreshCw, Compass } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const PUBLIC_ROUTES = ["/login", "/register"];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { status, isAuthenticated } = useAuth();
  const pathname = usePathname();

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

  // If on public auth routes, don't block
  if (isPublicRoute) {
    return <>{children}</>;
  }

  // If initializing session, show clean loading skeleton
  if (status === "INITIALIZING") {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center p-6 text-center space-y-4">
        <div className="w-12 h-12 rounded-full surface flex items-center justify-center text-soft-blue shadow-inner animate-pulse">
          <Compass className="w-6 h-6 animate-spin-slow" />
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-bold text-soft-text">Initializing Workspace</h3>
          <p className="text-xs text-soft-muted">Verifying your local authentication session...</p>
        </div>
      </div>
    );
  }

  // If unauthenticated on a protected workspace page (not home /)
  if (!isAuthenticated && pathname !== "/") {
    return (
      <div className="max-w-xl mx-auto my-12 px-4">
        <Card variant="surface" className="border border-slate-200/80 shadow-md">
          <CardHeader className="text-center pb-2">
            <div className="w-12 h-12 rounded-soft-lg bg-soft-blue/10 text-soft-blue flex items-center justify-center mx-auto mb-3">
              <Lock className="w-6 h-6" />
            </div>
            <CardTitle className="text-xl">Authentication Required</CardTitle>
            <CardDescription className="text-xs max-w-sm mx-auto">
              This module requires an authenticated workspace to safeguard your personal resume data, skills taxonomy, and job match records.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            <div className="well p-4 text-xs text-soft-muted space-y-2">
              <div className="flex items-center gap-2 font-semibold text-soft-text">
                <span>Local-First & Privacy Preserving</span>
              </div>
              <p>
                CareerPilot keeps your career assets private. Sign in to your local workspace or create an account in seconds.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
              <Link
                href={`/login?redirect=${encodeURIComponent(pathname)}`}
                className="w-full sm:w-1/2"
              >
                <Button variant="primary" className="w-full flex items-center justify-center gap-2">
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </Button>
              </Link>
              <Link
                href={`/register?redirect=${encodeURIComponent(pathname)}`}
                className="w-full sm:w-1/2"
              >
                <Button variant="soft" className="w-full flex items-center justify-center gap-2">
                  <UserPlus className="w-4 h-4" />
                  <span>Create Account</span>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
