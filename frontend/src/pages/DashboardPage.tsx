import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../services/api";
import {
  Files,
  Database,
  CopyX,
  Sparkles,
  Activity,
  History,
  AlertCircle
} from "lucide-react";
import { twMerge } from "tailwind-merge";
import { formatSize } from "../utils/format";

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
    refetchInterval: 10_000,
  });

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-slate-400">
          <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
          <p className="text-sm font-medium animate-pulse">正在加载概览数据...</p>
        </div>
      </div>
    );
  }

  const stats = [
    { label: "已索引文件", value: data?.total_files ?? 0, icon: Files, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "总文件大小", value: formatSize(data?.total_size ?? 0), icon: Database, color: "text-emerald-600", bg: "bg-emerald-50" },
    { label: "重复文件组", value: data?.duplicate_groups ?? 0, icon: CopyX, color: "text-amber-600", bg: "bg-amber-50" },
    { label: "待处理建议", value: data?.pending_suggestions ?? 0, icon: Sparkles, color: "text-blue-600", bg: "bg-blue-50" },
  ];

  return (
    <div className="max-w-6xl mx-auto animation-fade-in">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">工作台概览</h2>
        <p className="text-slate-500 mt-1">欢迎回来，这里是您的文件夹整理中心。</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-10">
        {stats.map((s) => (
          <div key={s.label} className="bg-white rounded-2xl border border-slate-200/60 p-6 shadow-sm hover:shadow-md transition-shadow duration-200 flex flex-col justify-between relative overflow-hidden group">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-sm font-medium text-slate-500">{s.label}</div>
                <div className="text-3xl font-bold text-slate-800 mt-2 tracking-tight">{s.value}</div>
              </div>
              <div className={twMerge("p-3 rounded-xl", s.bg)}>
                <s.icon className={twMerge("w-6 h-6", s.color)} strokeWidth={2} />
              </div>
            </div>
            <div className={twMerge("absolute -bottom-6 -right-6 opacity-0 group-hover:opacity-10 transition-opacity duration-300", s.color)}>
              <s.icon className="w-24 h-24" />
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Scan Tasks */}
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-5 border-b border-slate-100 flex items-center gap-2 bg-slate-50/50">
            <Activity className="w-5 h-5 text-slate-400" />
            <h3 className="text-base font-semibold text-slate-800">最近扫描任务</h3>
          </div>
          <div className="p-6 flex-1">
            {data?.recent_tasks?.length ? (
              <div className="space-y-4">
                {data.recent_tasks.map((t) => (
                  <div key={t.task_id} className="group flex items-start gap-4">
                    <div className="mt-1">
                      <div className={twMerge("w-2.5 h-2.5 rounded-full mt-1.5", statusDotColor(t.status))} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-slate-700 truncate" title={t.root_path}>
                          {t.root_path}
                        </span>
                        <span className={twMerge("px-2.5 py-0.5 rounded-md text-[11px] font-semibold tracking-wide whitespace-nowrap", statusBadgeColor(t.status))}>
                          {t.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-slate-400 text-xs mt-1 font-medium">
                        进度: <span className="text-slate-600">{t.scanned_files}</span> / {t.total_files} 文件
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 py-10">
                <AlertCircle className="w-10 h-10 mb-3 opacity-20" />
                <p className="text-sm">暂无扫描记录</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Operations */}
        <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden flex flex-col">
          <div className="px-6 py-5 border-b border-slate-100 flex items-center gap-2 bg-slate-50/50">
            <History className="w-5 h-5 text-slate-400" />
            <h3 className="text-base font-semibold text-slate-800">最近文件操作</h3>
          </div>
          <div className="p-6 flex-1">
            {data?.recent_operations?.length ? (
              <div className="space-y-4">
                {data.recent_operations.map((o) => (
                  <div key={o.id} className="group flex items-start gap-4">
                    <div className="mt-1">
                      <div className={twMerge("w-2.5 h-2.5 rounded-full mt-1.5", statusDotColor(o.status))} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-slate-700 truncate" title={o.source_path}>
                          {o.source_path.split(/[/\\]/).pop()}
                        </span>
                        <span className={twMerge("px-2.5 py-0.5 rounded-md text-[11px] font-semibold tracking-wide whitespace-nowrap", statusBadgeColor(o.status))}>
                          {o.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-slate-400 text-xs mt-1 font-medium flex items-center gap-1.5">
                        <span className="uppercase tracking-wider">{o.operation_type}</span>
                        <span className="text-slate-300">•</span>
                        <span className="truncate">{o.source_path}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 py-10">
                <AlertCircle className="w-10 h-10 mb-3 opacity-20" />
                <p className="text-sm">暂无操作记录</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function statusDotColor(status: string): string {
  switch (status) {
    case "completed":
    case "success": return "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]";
    case "running":
    case "pending": return "bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]";
    case "failed": return "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]";
    case "cancelled":
    case "rolled_back": return "bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)]";
    default: return "bg-slate-400";
  }
}

function statusBadgeColor(status: string): string {
  switch (status) {
    case "completed":
    case "success": return "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-600/20";
    case "running":
    case "pending": return "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/20";
    case "failed": return "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-600/20";
    case "cancelled":
    case "rolled_back": return "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20";
    default: return "bg-slate-50 text-slate-600 ring-1 ring-inset ring-slate-500/20";
  }
}
