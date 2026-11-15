"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UserCheck,
  FileUp,
  FileSearch,
  Scale,
  Sparkles,
  GraduationCap,
  MessageSquareCode,
  Kanban,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

const navItems: NavItem[] = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Master Profile", href: "/candidate", icon: UserCheck, badge: "Active" },
  { name: "Resume Ingestion", href: "/resumes", icon: FileUp },
  { name: "JD Intelligence", href: "/jobs", icon: FileSearch },
  { name: "Match Reports", href: "/matches", icon: Scale },
  { name: "AI Resume Optimizer", href: "/optimizer", icon: Sparkles, badge: "XYZ" },
  { name: "Learning Roadmaps", href: "/learning", icon: GraduationCap, badge: "AI" },
  { name: "Interview Prep", href: "/interview", icon: MessageSquareCode, badge: "STAR" },
  { name: "Application Pipeline", href: "/pipeline", icon: Kanban, badge: "Live" },
  { name: "Settings & LLM", href: "/settings", icon: Settings },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 surface ml-4 my-4 p-4 flex flex-col justify-between hidden lg:flex">
      <div className="space-y-6">
        <div className="px-3 pt-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-soft-muted">
            Intelligence Modules
          </span>
        </div>

        <nav className="space-y-1.5" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));

            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                  isActive
                    ? "well text-soft-blue font-semibold border-l-4 border-soft-blue"
                    : "text-soft-muted hover:text-soft-text hover:bg-white/40"
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className={cn("w-4 h-4", isActive ? "text-soft-blue" : "text-soft-muted")} />
                  <span>{item.name}</span>
                </div>
                {item.badge && (
                  <span
                    className={cn(
                      "text-[10px] px-2 py-0.5 rounded-full font-bold",
                      isActive
                        ? "bg-soft-blue text-white"
                        : "bg-slate-200 text-slate-700"
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="p-3 well rounded-2xl border border-white/60">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-soft-green animate-pulse" />
          <div className="text-xs">
            <p className="font-semibold text-soft-text">100% Free Engine</p>
            <p className="text-[11px] text-soft-muted">Local Ollama active</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
