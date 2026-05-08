import { request } from './client';

// AI Rule Drafts
export const createRuleDraft = (prompt: string) =>
  request<import("../../types").RuleDraftResponse>("/ai/rule-drafts", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });

export const previewRuleDraft = (draftId: number) =>
  request<import("../../types").PreviewResponse>(`/ai/rule-drafts/${draftId}/preview`);

export const acceptRuleDraft = (draftId: number) =>
  request<{ status: string; rule_id: number | null }>(`/ai/rule-drafts/${draftId}/accept`, {
    method: "POST",
  });

// Smart Organize
export const createClassificationTasks = (fileIds: number[]) =>
  request<{ task_id: number; status: string; queued_count: number }>("/ai/classify", {
    method: "POST",
    body: JSON.stringify({ file_ids: fileIds }),
  });

export const getAiTask = (taskId: number) =>
  request<any>(`/ai/tasks/${taskId}`);

export const createOrganizePlan = (scope: string, minConfidence: number = 0.65) =>
  request<{ task_id: number; status: string }>("/ai/organize-plans", {
    method: "POST",
    body: JSON.stringify({ scope, min_confidence: minConfidence }),
  });

export const getOrganizePlanPreview = (planId: number) =>
  request<any>(`/ai/organize-plans/${planId}`);

export const acceptOrganizePlan = (planId: number) =>
  request<{ status: string }>(`/ai/organize-plans/${planId}/accept`, {
    method: "POST"
  });

export const rejectOrganizePlan = (planId: number) =>
  request<{ status: string }>(`/ai/organize-plans/${planId}/reject`, {
    method: "POST"
  });

export const getExcludePaths = () =>
  request<{ exclude_paths: string[] }>("/ai/exclude-paths");

export const updateExcludePaths = (paths: string[]) =>
  request<{ status: string; exclude_paths: string[] }>("/ai/exclude-paths", {
    method: "POST",
    body: JSON.stringify({ exclude_paths: paths })
  });

// AI Summaries
export const createSummaryTask = (fileId: number) =>
  request<{ task_id: number; status: string }>("/ai/summaries", {
    method: "POST",
    body: JSON.stringify({ file_id: fileId }),
  });

export const getFileSummary = (fileId: number) =>
  request<any>(`/files/${fileId}/summary`);
