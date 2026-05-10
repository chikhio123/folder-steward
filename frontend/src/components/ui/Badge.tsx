import { HTMLAttributes } from "react";
import { cn } from "../../utils/cn";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: "primary" | "success" | "warning" | "danger" | "default";
}

export function Badge({ variant = "default", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-lg border font-mono text-xs tracking-wide",
        variant === "primary" && "text-blue-700 bg-blue-50 border-blue-200",
        variant === "success" && "text-emerald-700 bg-emerald-50 border-emerald-200",
        variant === "warning" && "text-amber-700 bg-amber-50 border-amber-200",
        variant === "danger" && "text-rose-700 bg-rose-50 border-rose-200",
        variant === "default" && "text-slate-600 bg-slate-50 border-slate-200",
        className
      )}
      {...props}
    />
  );
}