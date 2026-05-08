import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { createOrganizePlan, getOrganizePlanPreview, acceptOrganizePlan, rejectOrganizePlan, getAiTask, cancelAiTask } from '../services/api';
import toast from 'react-hot-toast';

export const useSmartOrganize = () => {
  const [archiveRoot, setArchiveRoot] = useState(() => localStorage.getItem("fs_last_archive_root") || "D:/Archive");
  const [scope, setScope] = useState("all");
  const [minConfidence, setMinConfidence] = useState<number | string>(0.65);
  const [showExcludeModal, setShowExcludeModal] = useState(false);
  const [taskId, setTaskId] = useState<number | null>(
    () => {
        const saved = localStorage.getItem("fs_task_id");
        if (!saved) return null;
        const val = parseInt(saved);
        if (isNaN(val)) {
            localStorage.removeItem("fs_task_id");
            return null;
        }
        return val;
    }
  );
  const [planId, setPlanId] = useState<number | null>(
    () => {
        const saved = localStorage.getItem("fs_plan_id");
        if (!saved) return null;
        const val = parseInt(saved);
        if (isNaN(val)) {
            localStorage.removeItem("fs_plan_id");
            return null;
        }
        return val;
    }
  );

  // Sync taskId to localStorage
  useEffect(() => {
    if (taskId !== null) {
      localStorage.setItem("fs_task_id", taskId.toString());
    } else {
      localStorage.removeItem("fs_task_id");
    }
  }, [taskId]);

  // Sync planId to localStorage
  useEffect(() => {
    if (planId !== null) {
      localStorage.setItem("fs_plan_id", planId.toString());
    } else {
      localStorage.removeItem("fs_plan_id");
    }
  }, [planId]);

  const planMutation = useMutation({
    mutationFn: () => createOrganizePlan(
      scope, 
      typeof minConfidence === "number" ? minConfidence : parseFloat(minConfidence as string) || 0
    ),
    onSuccess: (data: any) => {
      setTaskId(data.task_id);
      setPlanId(null);
      localStorage.setItem("fs_last_archive_root", archiveRoot);
      toast.success("AI 分类任务已提交后台处理");
    },
    onError: (err: any) => toast.error(`生成失败: ${err.message}`)
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelAiTask(taskId!),
    onSuccess: () => {
        toast.success("正在请求取消任务...");
    },
    onError: (err: any) => toast.error(`取消失败: ${err.message}`)
  });

  const { data: task } = useQuery({
    queryKey: ["ai-task", taskId],
    queryFn: () => getAiTask(taskId!),
    enabled: taskId !== null && planId === null,
    refetchInterval: (query: any) => {
      const s = query.state.data?.status;
      if (s === "pending" || s === "running") return 1000;
      return false;
    }
  });

  // Safely update planId outside of rendering phase
  useEffect(() => {
    if (task?.status === "completed" && task?.result_ref_id && planId === null) {
      setPlanId(task.result_ref_id);
    }
  }, [task, planId]);

  const { data: planData } = useQuery({
    queryKey: ["organize-plan", planId],
    queryFn: () => getOrganizePlanPreview(planId!),
    enabled: planId !== null,
  });

  const acceptMutation = useMutation({
    mutationFn: () => acceptOrganizePlan(planId!),
    onSuccess: () => {
      toast.success("整理方案已成功转化为实际移动建议！");
      setTaskId(null);
      setPlanId(null);
    },
    onError: (err: any) => toast.error(`确认失败: ${err.message}`)
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectOrganizePlan(planId!),
    onSuccess: () => {
      toast.success("已拒绝此整理方案，释放所有分类建议");
      setTaskId(null);
      setPlanId(null);
    },
    onError: (err: any) => toast.error(`拒绝失败: ${err.message}`)
  });

  // Cleanup on task failure
  useEffect(() => {
    if (task?.status === "failed" || task?.status === "rate_limited") {
      setTaskId(null);
      setPlanId(null);
    }
  }, [task?.status]);

  const isRunning = task?.status === "running" || task?.status === "pending" || planMutation.isPending;

  return {
    state: { archiveRoot, scope, minConfidence, showExcludeModal, taskId, planId, isRunning, task, planData },
    actions: { setArchiveRoot, setScope, setMinConfidence, setShowExcludeModal, setTaskId, setPlanId },
    mutations: { planMutation, cancelMutation, acceptMutation, rejectMutation }
  };
};