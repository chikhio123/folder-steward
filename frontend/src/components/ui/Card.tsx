import { ReactNode } from "react";
import { cn } from "../../utils/cn";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: "solid" | "glass" | "bordered";
}

export function Card({ children, variant = "solid", className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border shadow-sm transition-all duration-300",
        variant === "solid" && "bg-white border-slate-200/60",
        variant === "glass" && "bg-white/80 backdrop-blur-xl border-slate-200/60",
        variant === "bordered" && "bg-transparent border-slate-200/60",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}