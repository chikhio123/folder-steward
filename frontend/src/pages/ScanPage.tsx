import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createScanTask, getScanTask, getScanErrors, cancelScanTask } from "../services/api";
export default function ScanPage() {
  const queryClient = useQueryClient();
  const [path, setPath] = useState("");
  const [taskId, setTaskId] = useState<number | null>(null);

  const createMutation = useMutation({
    mutationFn: () => createScanTask(path),
    onSuccess: (data) => setTaskId(data.task_id),
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelScanTask(taskId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scan-task", taskId] });
    },
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

  const isRunning = task?.status === "running" || task?.status === "pending";

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-800 mb-6">扫描文件夹</h2>

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">文件夹路径</label>
        <div className="flex gap-3">
          <input
            type="text"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="例如：D:/Downloads"
            className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isRunning}
          />
          <button
            onClick={() => createMutation.mutate()}
            disabled={!path.trim() || isRunning}
            className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createMutation.isPending ? "创建中..." : "开始扫描"}
          </button>
        </div>
        {createMutation.isError && (
          <p className="text-red-600 text-sm mt-2">{(createMutation.error as Error).message}</p>
        )}
      </div>

      {task && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-medium text-gray-800 mb-4">扫描进度</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">状态</span>
              <div className="flex items-center gap-3">
                <span className={`font-medium ${statusColor(task.status)}`}>{statusLabel(task.status)}</span>
                {(task.status === "running" || task.status === "pending") && (
                  <button
                    onClick={() => cancelMutation.mutate()}
                    disabled={cancelMutation.isPending}
                    className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-md hover:bg-red-200 disabled:opacity-50"
                  >
                    {cancelMutation.isPending ? "取消中..." : "取消扫描"}
                  </button>
                )}
              </div>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">进度</span>
              <span className="text-gray-700">
                {task.scanned_files} / {task.total_files || "?"}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{
                  width: task.total_files > 0 ? `${(task.scanned_files / task.total_files) * 100}%` : "0%",
                }}
              />
            </div>
            {task.failed_files > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-red-500">失败文件</span>
                <span className="text-red-500">{task.failed_files}</span>
              </div>
            )}
            {task.error_message && (
              <p className="text-red-600 text-sm mt-2">{task.error_message}</p>
            )}
            {cancelMutation.isError && (
              <p className="text-red-600 text-sm mt-2">{(cancelMutation.error as Error).message}</p>
            )}
          </div>
        </div>
      )}

      {(task?.status === "completed" || task?.status === "failed") && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-medium text-gray-800">扫描错误</h3>
            <button onClick={() => refetchErrors()} className="text-sm text-blue-600 hover:text-blue-800">
              加载错误详情
            </button>
          </div>
          {errorData?.items?.length ? (
            <div className="space-y-2">
              {errorData.items.map((e, i) => (
                <div key={i} className="text-sm text-red-600 bg-red-50 rounded p-2">
                  <span className="font-medium">{e.file_path}</span>: {e.error_message}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">无扫描错误</p>
          )}
        </div>
      )}
    </div>
  );
}

function statusLabel(status: string): string {
  switch (status) {
    case "pending": return "等待中";
    case "running": return "扫描中";
    case "completed": return "已完成";
    case "failed": return "失败";
    case "cancelled": return "已取消";
    default: return status;
  }
}

function statusColor(status: string): string {
  switch (status) {
    case "completed": return "text-green-600";
    case "running":
    case "pending": return "text-blue-600";
    case "failed": return "text-red-600";
    case "cancelled": return "text-yellow-600";
    default: return "text-gray-600";
  }
}
