import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createScanTask, getScanTask, getScanErrors, cancelScanTask } from "../../../services/api";
import toast from "react-hot-toast";

export function useScanTask() {
  const queryClient = useQueryClient();
  const [path, setPath] = useState(() => localStorage.getItem("fs_last_scan_path") || "");
  const [taskId, setTaskId] = useState<number | null>(() => {
    const saved = localStorage.getItem("fs_active_scan_task_id");
    if (!saved) return null;
    const parsed = parseInt(saved, 10);
    return isNaN(parsed) ? null : parsed;
  });

  // Save path to local storage whenever it changes
  useEffect(() => {
    if (path.trim()) {
      localStorage.setItem("fs_last_scan_path", path.trim());
    }
  }, [path]);

  const createMutation = useMutation({
    mutationFn: () => createScanTask(path),
    onSuccess: (data) => {
      setTaskId(data.task_id);
      localStorage.setItem("fs_active_scan_task_id", data.task_id.toString());
    },
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelScanTask(taskId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scan-task", taskId] });
      toast.success("已发送停止扫描指令");
    },
    onError: (err) => toast.error(`无法停止扫描: ${err.message}`)
  });

  const taskQuery = useQuery({
    queryKey: ["scan-task", taskId],
    queryFn: () => getScanTask(taskId!),
    enabled: taskId !== null,
    refetchInterval: (query) =>
      query.state.data?.status === "running" || query.state.data?.status === "pending" ? 1000 : false,
  });

  // Clear persisted task if it finishes or errors out (404)
  useEffect(() => {
    if (taskQuery.isError) {
      setTaskId(null);
      localStorage.removeItem("fs_active_scan_task_id");
    } else if (
      taskQuery.data?.status === "completed" ||
      taskQuery.data?.status === "failed" ||
      taskQuery.data?.status === "cancelled"
    ) {
      localStorage.removeItem("fs_active_scan_task_id");
    }
  }, [taskQuery.data?.status, taskQuery.isError]);

  const errorQuery = useQuery({
    queryKey: ["scan-errors", taskId],
    queryFn: () => getScanErrors(taskId!),
    enabled: taskQuery.data?.status === "completed" || taskQuery.data?.status === "failed",
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

  const isRunning = taskQuery.data?.status === "running" || taskQuery.data?.status === "pending";

  return {
    path,
    setPath,
    taskId,
    isRunning,
    handleSelectDirectory,
    taskQuery,
    errorQuery,
    createMutation,
    cancelMutation
  };
}