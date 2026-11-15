"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Compass, ShieldCheck, User, LogIn, LogOut, Settings, UserPlus } from "lucide-react";
import { OllamaStatusWidget } from "@/components/ui/ollama-status";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/context/AuthContext";

export const Header: React.FC = () => {
  const { user, isAuthenticated, logout, isLoading } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const getInitials = () => {
    if (!user) return "CP";
    if (user.full_name && user.full_name.trim()) {
      const parts = user.full_name.trim().split(/\s+/);
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return parts[0].slice(0, 2).toUpperCase();
    }
    return user.email.slice(0, 2).toUpperCase();
  };

  const displayName = user?.full_name || (user?.email ? user.email.split("@")[0] : "Workspace");

  return (
    <header className="h-16 surface mx-4 mt-4 px-6 flex items-center justify-between sticky top-4 z-40">
      <Link href="/" className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-soft-md bg-soft-blue flex items-center justify-center text-white shadow-md">
          <Compass className="w-5 h-5 animate-spin-slow" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-base tracking-tight text-soft-text">
              CareerPilot
            </span>
            <Badge variant="info" className="text-[10px] py-0">
              v1.0 Local MVP
            </Badge>
          </div>
          <p className="text-[11px] text-soft-muted hidden sm:block">
            Navigate your career. Engineer your future.
          </p>
        </div>
      </Link>

      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-1.5 text-xs text-soft-muted mr-2">
          <ShieldCheck className="w-4 h-4 text-soft-green-text" />
          <span>Factual Integrity: Guaranteed</span>
        </div>

        {/* Ollama Real-Time Status Widget */}
        <OllamaStatusWidget />

        {/* User Auth Section */}
        {isLoading ? (
          <div className="w-24 h-8 well animate-pulse rounded-soft-md" />
        ) : isAuthenticated ? (
          <div className="relative">
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="btn-soft flex items-center gap-2 px-3 py-1.5 text-xs font-semibold"
              aria-label="User Workspace Profile"
            >
              <div className="w-5 h-5 rounded-full bg-soft-blue/20 text-soft-blue flex items-center justify-center font-bold text-[10px]">
                {getInitials()}
              </div>
              <span className="hidden sm:inline truncate max-w-[120px]">{displayName}</span>
            </button>

            {menuOpen && (
              <div
                className="absolute right-0 mt-2 w-48 surface border border-slate-200/80 rounded-soft-md shadow-lg p-2 z-50 space-y-1"
                onMouseLeave={() => setMenuOpen(false)}
              >
                <div className="px-3 py-2 border-b border-slate-200/60 text-[11px] text-soft-muted truncate">
                  {user?.email}
                </div>
                <Link
                  href="/settings"
                  onClick={() => setMenuOpen(false)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-soft-text hover:text-soft-blue rounded-soft-sm hover:bg-slate-100/50 transition-colors"
                >
                  <Settings className="w-3.5 h-3.5" />
                  <span>Master Profile</span>
                </Link>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-soft-orange-text hover:bg-red-50/50 rounded-soft-sm transition-colors text-left"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="btn-soft flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-soft-text"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </Link>
            <Link
              href="/register"
              className="btn-primary flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Register</span>
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
