import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "soft" | "primary" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "soft", size = "md", children, ...props }, ref) => {
    const sizeClasses = {
      sm: "px-3 py-1.5 text-xs rounded-soft-sm",
      md: "px-4 py-2 text-sm rounded-soft-md",
      lg: "px-6 py-3 text-base rounded-soft-lg",
    };

    const variantClasses = {
      soft: "btn-soft",
      primary: "btn-primary",
      ghost: "hover:bg-slate-200/50 text-soft-text transition-colors",
      outline: "border border-soft-blue text-soft-blue hover:bg-soft-blue/10 transition-colors",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-soft-blue focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none",
          sizeClasses[size],
          variantClasses[variant],
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
