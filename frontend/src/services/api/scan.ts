import { request } from './client';

export const createScanTask = (rootPath: string) =>
  request<{ task_id: number; status: string }>("/scan-tasks", {
    method: "POST",
    body: JSON.stringify({ root_path: rootPath }),
  });

export const getScanTask = (taskId: number) =>
  request<import("../../types").ScanTask>(`/scan-tasks/${taskId}`);

export const cancelScanTask = (taskId: number) =>
  request<{ task_id: number; status: string }>(`/scan-tasks/${taskId}/cancel`, {
    method: "POST",
  });

export const getScanErrors = (taskId: number) =>
  request<{ items: import("../../types").ScanError[] }>(`/scan-tasks/${taskId}/errors`);
