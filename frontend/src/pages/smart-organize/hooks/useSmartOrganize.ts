import { useSmartOrganizeFormState } from './useSmartOrganizeFormState';
import { useTaskLifecycleState } from './useTaskLifecycleState';
import { useOrganizeQueries } from './useOrganizeQueries';

export const useSmartOrganize = () => {
  const form = useSmartOrganizeFormState();
  const lifecycle = useTaskLifecycleState();
  
  const queries = useOrganizeQueries({
    taskId: lifecycle.taskId,
    planId: lifecycle.planId,
    callbacks: {
      onTaskCreated: lifecycle.startTask,
      onPlanReady: lifecycle.setPlanId,
      onClear: lifecycle.clearTasks
    }
  });

  const isRunning = 
    queries.taskQuery.data?.status === "running" || 
    queries.taskQuery.data?.status === "pending" || 
    queries.planMutation.isPending;

  return {
    state: {
      ...form,
      taskId: lifecycle.taskId,
      planId: lifecycle.planId,
      isRunning,
      task: queries.taskQuery.data,
      planData: queries.planQuery.data
    },
    actions: {
      setArchiveRoot: form.setArchiveRoot,
      setScope: form.setScope,
      setMinConfidence: form.setMinConfidence,
      setShowExcludeModal: form.setShowExcludeModal,
      setTaskId: lifecycle.setTaskId,
      setPlanId: lifecycle.setPlanId
    },
    mutations: {
      planMutation: queries.planMutation,
      cancelMutation: queries.cancelMutation,
      acceptMutation: queries.acceptMutation,
      rejectMutation: queries.rejectMutation
    }
  };
};