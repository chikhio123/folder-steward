import { useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { createOrganizePlan, getOrganizePlanPreview, acceptOrganizePlan, rejectOrganizePlan, getAiTask, cancelAiTask } from '../../../services/api';
import toast from 'react-hot-toast';

interface OrganizeQueriesProps {
  taskId: number | null;
  planId: number | null;
  callbacks: {
    onTaskCreated: (taskId: number) => void;
    onPlanReady: (planId: number) => void;
    onClear: () => void;
  };
}

export const useOrganizeQueries = ({ taskId, planId, callbacks }: OrganizeQueriesProps) => {

  const planMutation = useMutation({
    mutationFn: (variables: { scope: string, minConfidence: number, archiveRoot: string }) => 
      createOrganizePlan(variables.scope, variables.minConfidence),
    onSuccess: (data, variables) => {
      callbacks.onTaskCreated(data.task_id);
      localStorage.setItem("fs_last_archive_root", variables.archiveRoot);
      toast.success("AI 分类任务已提交后台处理");
    },
    onError: (err: Error) => toast.error(`生成失败: ${err.message}`)
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelAiTask(taskId!),
    onSuccess: () => {
        toast.success("正在请求取消任务...");
    },
    onError: (err: Error) => toast.error(`取消失败: ${err.message}`)
  });

  const taskQuery = useQuery({
    queryKey: ["ai-task", taskId],
    queryFn: () => getAiTask(taskId!),
    enabled: taskId !== null && planId === null,
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      if (s === "pending" || s === "running") return 1000;
      return false;
    }
  });

  // Safely update planId outside of rendering phase when task completes
  const { onPlanReady } = callbacks;
  useEffect(() => {
    if (taskQuery.data?.status === "completed" && taskQuery.data?.result_ref_id && planId === null) {
      onPlanReady(taskQuery.data.result_ref_id);
    }
  }, [taskQuery.data, planId, onPlanReady]);

  const planQuery = useQuery({
    queryKey: ["organize-plan", planId],
    queryFn: () => getOrganizePlanPreview(planId!),
    enabled: planId !== null,
  });

  const acceptMutation = useMutation({
    mutationFn: () => acceptOrganizePlan(planId!),
    onSuccess: () => {
      toast.success("整理方案已成功转化为实际移动建议！");
      callbacks.onClear();
    },
    onError: (err: Error) => toast.error(`确认失败: ${err.message}`)
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectOrganizePlan(planId!),
    onSuccess: () => {
      toast.success("已拒绝此整理方案，释放所有分类建议");
      callbacks.onClear();
    },
    onError: (err: Error) => toast.error(`拒绝失败: ${err.message}`)
  });

  return {
    taskQuery,
    planQuery,
    planMutation,
    cancelMutation,
    acceptMutation,
    rejectMutation
  };
};