import { useState, useEffect } from 'react';

export const useTaskLifecycleState = () => {
  const [taskId, setTaskId] = useState<number | null>(() => {
    const saved = localStorage.getItem("fs_task_id");
    if (!saved) return null;
    const val = parseInt(saved);
    if (isNaN(val)) {
      localStorage.removeItem("fs_task_id");
      return null;
    }
    return val;
  });

  const [planId, setPlanId] = useState<number | null>(() => {
    const saved = localStorage.getItem("fs_plan_id");
    if (!saved) return null;
    const val = parseInt(saved);
    if (isNaN(val)) {
      localStorage.removeItem("fs_plan_id");
      return null;
    }
    return val;
  });

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

  const clearTasks = () => {
    setTaskId(null);
    setPlanId(null);
  };

  return {
    taskId,
    setTaskId,
    planId,
    setPlanId,
    clearTasks
  };
};