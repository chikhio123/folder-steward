import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createScanTask, getScanTask, getScanErrors, cancelScanTask } from "../services/api";
import { FolderSearch, Play, Square, AlertCircle, ChevronRight, CheckCircle2, FileText, Loader2, FolderInput } from "lucide-react";
import { twMerge } from "tailwind-merge";
import toast from "react-hot-toast";

export default function ScanPage() {
  const queryClient = useQueryClient();
  const [path, setPath] = useState(() => localStorage.getItem("fs_last_scan_path") || "");
  const [taskId, setTaskId] = useState<number | null>(null);

  // Save path to local storage whenever it changes
  useEffect(() => {
    if (path.trim()) {
      localStorage.setItem("fs_last_scan_path", path.trim());
    }
  }, [path]);

  const createMutation = useMutation({
    mutationFn: () => createScanTask(path),
    onSuccess: (data) => setTaskId(data.task_id),
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelScanTask(taskId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scan-task", taskId] });
      toast.success("已发送停止扫描指令");
    },
    onError: (err) => toast.error(`无法停止扫描: ${err.message}`)
  });

  const { data: task } = useQuery({
    queryKey: ["scan-task", taskId],
    queryFn: () => getScanTask(taskId!),
    enabled: taskId !== null,
    refetchInterval: (query) =>
      query.state.data?.status === "running" || query.state.data?.status === "pending" ? 1000 : false,
  });

  const { data: errorData, refetch: refetchErrors } = useQuery({
    queryKey: ["scan-errors", taskId],
    queryFn: () => getScanErrors(taskId!),
    enabled: task?.status === "completed" || task?.status === "failed",
  });

  const handleSelectDirectory = async () => {
    if (window.electronAPI?.selectDirectory) {
      const dirPath = await window.electronAPI.selectDirectory();
      if (dirPath) {
        setPath(dirPath);
      }
    } else {
      toast.error("当前不在 Electron 桌面环境中，无法打开系统文件夹选择器");
    }
  };

  const isRunning = task?.status === "running" || task?.status === "pending";

  return (
    <div className="max-w-4xl mx-auto animation-fade-in">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">扫描文件夹</h2>
        <p className="text-slate-500 mt-1">选择一个目录进行深度扫描，建立本地文件索引并生成整理建议。</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200/60 p-8 mb-6 shadow-sm">
        <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 mb-3">
          <FolderSearch className="w-4 h-4 text-blue-600" />
          目标文件夹路径
        </label>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="例如：D:/Downloads 或 /Users/name/Downloads"
              className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-xl px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all placeholder:text-slate-400"
              disabled={isRunning}
            />
            {isRunning && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2">
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              </div>
            )}
            {!isRunning && window.electronAPI?.selectDirectory && (
              <button
                type="button"
                onClick={handleSelectDirectory}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                title="选择文件夹"
              >
                <FolderInput className="w-5 h-5" />
              </button>
            )}
          </div>
          <button
            onClick={() => createMutation.mutate()}
            disabled={!path.trim() || isRunning}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl text-sm font-semibold shadow-sm shadow-blue-600/20 hover:bg-blue-700 hover:shadow-md hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center justify-center gap-2 min-w-[140px]"
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                准备中
              </>
            ) : (
              <>
                <Play className="w-4 h-4" fill="currentColor" />
                开始扫描
              </>
            )}
          </button>
        </div>
        {createMutation.isError && (
          <div className="mt-3 flex items-center gap-2 text-rose-600 bg-rose-50 px-3 py-2 rounded-lg text-sm border border-rose-100">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <p>{(createMutation.error as Error).message}</p>
          </div>
        )}
      </div>

      {task && (
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
                  onClick={() => cancelMutation.mutate()}
                  disabled={cancelMutation.isPending}
                  className="px-3 py-1.5 flex items-center gap-1.5 text-xs font-semibold bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 hover:text-slate-900 disabled:opacity-50 transition-colors"
                >
                  <Square className="w-3.5 h-3.5" fill="currentColor" />
                  {cancelMutation.isPending ? "正在停止..." : "停止扫描"}
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
            {cancelMutation.isError && (
              <p className="text-rose-600 text-sm">{(cancelMutation.error as Error).message}</p>
            )}
          </div>
        </div>
      )}

      {(task?.status === "completed" || task?.status === "failed") && (
        <div className="bg-white rounded-2xl border border-slate-200/60 p-8 shadow-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
              <FileText className="w-5 h-5 text-slate-400" />
              扫描报告
            </h3>
            {task.failed_files > 0 && (
              <button
                onClick={() => refetchErrors()}
                className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1 transition-colors"
              >
                加载错误日志
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>

          {errorData?.items?.length ? (
            <div className="space-y-3 mt-4">
              {errorData.items.map((e, i) => (
                <div key={i} className="text-sm text-rose-700 bg-rose-50/50 rounded-xl p-4 border border-rose-100">
                  <div className="font-semibold mb-1 break-all flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    {e.file_path}
                  </div>
                  <div className="text-rose-600/80 ml-6">{e.error_message}</div>
                </div>
              ))}
            </div>
          ) : task.failed_files > 0 ? (
            <p className="text-slate-500 text-sm mt-2">点击上方按钮加载错误详情...</p>
          ) : (
            <div className="flex flex-col items-center justify-center py-6 text-slate-500">
              <CheckCircle2 className="w-12 h-12 text-emerald-400 mb-3 opacity-50" />
              <p className="text-sm font-medium">太棒了，没有任何扫描错误！</p>
            </div>
          )}
        </div>
      )}
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
