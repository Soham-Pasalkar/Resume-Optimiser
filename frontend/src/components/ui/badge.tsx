import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "success" | "warning" | "info" | "neutral";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "neutral",
  children,
  ...props
}) => {
  const variantClasses = {
    success:
      "bg-soft-green-subtle text-soft-green-text border border-green-300/60",
    warning:
      "bg-soft-orange-subtle text-soft-orange-text border border-orange-300/60",
    info: "bg-soft-blue-subtle text-soft-blue border border-blue-300/60",
    neutral: "bg-slate-200/60 text-soft-text border border-slate-300/60",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide select-none",
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};
