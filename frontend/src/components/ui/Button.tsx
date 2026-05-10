import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "../../utils/cn";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "ghost" | "outline" | "danger-soft";
  size?: "sm" | "md" | "lg" | "icon";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none focus:outline-none focus:ring-2 focus:ring-offset-2",
          // Variants
          variant === "primary" && "bg-blue-600 text-white hover:bg-blue-700 shadow-sm shadow-blue-600/20 focus:ring-blue-500",
          variant === "secondary" && "bg-slate-100 text-slate-700 hover:bg-slate-200 focus:ring-slate-500",
          variant === "danger" && "bg-rose-600 text-white hover:bg-rose-700 shadow-sm shadow-rose-600/20 focus:ring-rose-500",
          variant === "danger-soft" && "text-rose-600 bg-rose-50 hover:bg-rose-100 border border-rose-100 focus:ring-rose-500",
          variant === "outline" && "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900 shadow-sm focus:ring-slate-500",
          variant === "ghost" && "text-slate-600 hover:bg-slate-100 focus:ring-slate-500",
          // Sizes
          size === "sm" && "px-3 py-1.5 text-xs rounded-lg gap-1.5",
          size === "md" && "px-4 py-2 text-sm rounded-xl gap-2",
          size === "lg" && "px-6 py-2.5 text-base rounded-xl gap-2.5",
          size === "icon" && "p-1.5 rounded-lg",
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";