import { Square, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { twMerge } from "tailwind-merge";
import type { ScanTask } from "../types";

export interface ScanProgressCardProps {
  task: ScanTask;
  onCancel: () => void;
  isCancelling: boolean;
  cancelError?: Error | null;
}

export function ScanProgressCard({ task, onCancel, isCancelling, cancelError }: ScanProgressCardProps) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/60 p-8 mb-6 shadow-sm transition-all duration-300">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <ActivityIcon status={task.status} />
          扫描进度
        </h3>
        <div className="flex items-center gap-3">
          <span className={twMerge("px-3 py-1 rounded-full text-xs font-bold tracking-wide", statusBadgeColor(task.status))}>
            {statusLabel(task.status)}
          </span>
          {(task.status === "running" || task.status === "pending") && (
            <button
              onClick={onCancel}
              disabled={isCancelling}
              className="px-3 py-1.5 flex items-center gap-1.5 text-xs font-semibold bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 hover:text-slate-900 disabled:opacity-50 transition-colors"
            >
              <Square className="w-3.5 h-3.5" fill="currentColor" />
              {isCancelling ? "正在停止..." : "停止扫描"}
            </button>
          )}
        </div>
      </div>

      <div className="space-y-6">
        <div>
          <div className="flex justify-between text-sm font-medium mb-2">
            <span className="text-slate-500">已处理文件</span>
            <span className="text-slate-800">
              {task.scanned_files} <span className="text-slate-400 font-normal">/ {task.total_files || "?"}</span>
            </span>
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden ring-1 ring-inset ring-slate-200/50">
            <div
              className={twMerge("h-full rounded-full transition-all duration-500 ease-out relative",
                task.status === "completed" ? "bg-emerald-500" : task.status === "failed" ? "bg-rose-500" : "bg-blue-500"
              )}
              style={{
                width: task.total_files > 0 ? `${(task.scanned_files / task.total_files) * 100}%` : "0%",
              }}
            >
              {(task.status === "running" || task.status === "pending") && (
                <div className="absolute top-0 left-0 right-0 bottom-0 bg-white/20 animate-pulse"></div>
              )}
            </div>
          </div>
        </div>

        {task.failed_files > 0 && (
          <div className="flex items-center gap-2 text-sm text-rose-600 bg-rose-50 px-4 py-2.5 rounded-lg border border-rose-100/50">
            <AlertCircle className="w-4 h-4" />
            <span className="font-medium">遇到错误的文件数量：</span>
            <span className="font-bold">{task.failed_files}</span>
          </div>
        )}
        {task.error_message && (
          <div className="text-rose-600 text-sm bg-rose-50 p-4 rounded-xl border border-rose-100">
            <strong>严重错误：</strong> {task.error_message}
          </div>
        )}
        {cancelError && (
          <p className="text-rose-600 text-sm">{cancelError.message}</p>
        )}
      </div>
    </div>
  );
}

function ActivityIcon({ status }: { status: string }) {
  if (status === "running" || status === "pending") return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
  if (status === "completed") return <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
  if (status === "failed") return <AlertCircle className="w-5 h-5 text-rose-500" />;
  return <Square className="w-5 h-5 text-slate-400" />;
}

function statusLabel(status: string): string {
  switch (status) {
    case "pending": return "准备中";
    case "running": return "扫描中";
    case "completed": return "扫描完成";
    case "failed": return "扫描失败";
    case "cancelled": return "已终止";
    default: return status;
  }
}

function statusBadgeColor(status: string): string {
  switch (status) {
    case "completed": return "bg-emerald-100 text-emerald-700";
    case "running":
    case "pending": return "bg-blue-100 text-blue-700";
    case "failed": return "bg-rose-100 text-rose-700";
    case "cancelled": return "bg-slate-100 text-slate-700";
    default: return "bg-slate-100 text-slate-600";
  }
}