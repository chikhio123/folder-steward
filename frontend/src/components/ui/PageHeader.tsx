import { ReactNode } from "react";
import { cn } from "../../utils/cn";

export interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({ title, description, icon, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8", className)}>
      <div className="flex items-center gap-3">
        {icon && (
          <div className="p-2.5 bg-white rounded-xl shadow-sm border border-slate-200/60 shrink-0">
            {icon}
          </div>
        )}
        <div>
          <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-400 tracking-tight pb-1">
            {title}
          </h2>
          {description && (
            <p className="text-slate-500 mt-1 font-medium">{description}</p>
          )}
        </div>
      </div>
      {actions && (
        <div className="flex items-center gap-3 flex-wrap">
          {actions}
        </div>
      )}
    </div>
  );
}