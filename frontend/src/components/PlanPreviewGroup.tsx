import { FolderTree, FileBox, AlertCircle, ArrowRight, ShieldAlert } from 'lucide-react';
import { twMerge } from 'tailwind-merge';
import type { OrganizePlanItem } from '../types';

export function PlanPreviewGroup({ dir, items }: { dir: string, items: OrganizePlanItem[] }) {
  const isExcluded = items.some(item => item.directory_status === "excluded");
  
  return (
    <div className="bg-white rounded-2xl border border-slate-200/60 p-6 shadow-sm">
      <h4 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2">
        <FolderTree className="w-5 h-5 text-blue-500" />
        {dir}
        <span className="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md">
          {items.length} 个文件
        </span>
        {isExcluded && (
          <span className="ml-auto flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md font-medium bg-rose-50 text-rose-600 border border-rose-200/60">
            <ShieldAlert className="w-3.5 h-3.5" />
            包含排除目录
          </span>
        )}
      </h4>
      <div className="space-y-3">
        {items.map((item, idx: number) => (
          <div key={idx} className={twMerge(
            "p-4 rounded-xl border transition-colors",
            item.directory_status === "excluded" 
              ? "bg-rose-50/50 border-rose-100" 
              : "bg-slate-50 border-slate-100 hover:border-slate-200 hover:bg-slate-50/80"
          )}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <FileBox className={twMerge(
                    "w-4 h-4 shrink-0",
                    item.directory_status === "excluded" ? "text-rose-400" : "text-slate-400"
                  )} />
                  <span className={twMerge(
                    "text-sm font-semibold truncate",
                    item.directory_status === "excluded" ? "text-rose-700" : "text-slate-700"
                  )}>
                    {item.source_path.split(/[/\\]/).pop()}
                  </span>
                  <span className={twMerge(
                    "text-[10px] px-1.5 py-0.5 rounded font-medium",
                    item.confidence >= 0.8 ? "bg-emerald-100 text-emerald-700" :
                    item.confidence >= 0.5 ? "bg-blue-100 text-blue-700" : "bg-amber-100 text-amber-700"
                  )}>
                    {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-xs">
                  <span className="text-slate-400 truncate max-w-[40%]" title={item.source_path}>
                    {item.source_path}
                  </span>
                  <ArrowRight className="w-3 h-3 text-blue-400 shrink-0" />
                  <span className="text-blue-600 font-medium truncate flex-1" title={item.target_path}>
                    {item.target_path}
                  </span>
                </div>
                {item.reason ? (
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <div className="text-xs text-slate-500 bg-white/60 px-3 py-1.5 rounded-lg inline-block border border-slate-200/40">
                      <span className="font-semibold text-slate-600 mr-1">AI 判断：</span>
                      {item.reason}
                    </div>
                    {item.directory_status === "proposed_new" && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-600 border border-amber-200">
                        拟建新目录
                      </span>
                    )}
                  </div>
                ) : (
                  item.directory_status === "proposed_new" && (
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-600 border border-amber-200">
                        拟建新目录
                      </span>
                    </div>
                  )
                )}
              </div>
              {item.directory_status === "excluded" && (
                <div className="shrink-0 flex flex-col items-end gap-1">
                  <span className="flex items-center gap-1 text-[11px] px-2 py-1 rounded bg-white text-rose-600 border border-rose-200 font-medium shadow-sm">
                    <AlertCircle className="w-3 h-3" />
                    将被跳过
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}