"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  UserCheck,
  FileSearch,
  Scale,
  Sparkles,
  GraduationCap,
  MessageSquareCode,
  Kanban,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavGroup {
  label: string;
  items: {
    name: string;
    href: string;
    icon: React.ElementType;
    badge?: string;
  }[];
}

const navGroups: NavGroup[] = [
  {
    label: "Workspace",
    items: [
      { name: "Overview", href: "/", icon: LayoutDashboard },
      { name: "My Career Profile", href: "/candidate", icon: UserCheck },
      { name: "Analyze a Job", href: "/jobs", icon: FileSearch },
      { name: "Gap Analysis", href: "/matches", icon: Scale },
      { name: "Resume Studio", href: "/optimizer", icon: Sparkles, badge: "Studio" },
    ],
  },
  {
    label: "Career Development",
    items: [
      { name: "Learning & Projects", href: "/learning", icon: GraduationCap },
      { name: "Interview Preparation", href: "/interview", icon: MessageSquareCode },
      { name: "Application Tracker", href: "/pipeline", icon: Kanban },
    ],
  },
  {
    label: "Settings",
    items: [{ name: "Settings", href: "/settings", icon: Settings }],
  },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside className="w-64 surface ml-4 my-4 p-4 flex flex-col justify-between hidden lg:flex rounded-2xl border border-slate-200/60 shadow-sm">
      <div className="space-y-6">
        {navGroups.map((group) => (
          <div key={group.label} className="space-y-2">
            <div className="px-3">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-soft-muted">
                {group.label}
              </span>
            </div>

            <nav className="space-y-1" aria-label={group.label}>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.href === "/"
                    ? pathname === "/"
                    : pathname === item.href || pathname.startsWith(`${item.href}/`);

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-150",
                      isActive
                        ? "well text-soft-blue border-l-4 border-soft-blue shadow-inner"
                        : "text-soft-muted hover:text-soft-text hover:bg-slate-100/60"
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon
                        className={cn(
                          "w-4 h-4 transition-colors",
                          isActive ? "text-soft-blue" : "text-soft-muted"
                        )}
                      />
                      <span>{item.name}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={cn(
                          "text-[9px] px-1.5 py-0.5 rounded-full font-bold uppercase",
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
        ))}
      </div>

      <div className="p-3 well rounded-xl border border-slate-200/50">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-soft-green animate-pulse" />
          <div className="text-xs">
            <p className="font-bold text-soft-text">Zero-Cost AI Engine</p>
            <p className="text-[10px] text-soft-muted">Local Ollama • Privacy First</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
