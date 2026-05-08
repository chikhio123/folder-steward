import { request } from './api/client';

export * from './api/client';
export * from './api/system';

// Scan tasks
export const createScanTask = (rootPath: string) =>
  request<{ task_id: number; status: string }>("/scan-tasks", {
    method: "POST",
    body: JSON.stringify({ root_path: rootPath }),
  });

export const getScanTask = (taskId: number) =>
  request<import("../types").ScanTask>(`/scan-tasks/${taskId}`);

export const cancelScanTask = (taskId: number) =>
  request<{ task_id: number; status: string }>(`/scan-tasks/${taskId}/cancel`, {
    method: "POST",
  });

export const getScanErrors = (taskId: number) =>
  request<{ items: import("../types").ScanError[] }>(`/scan-tasks/${taskId}/errors`);

// Extraction
export const forceExtractFile = (fileId: number) =>
  request<{ created_count: number; skipped_count: number }>("/extract-tasks", {
    method: "POST",
    body: JSON.stringify({ file_ids: [fileId], mode: "force" }),
  });

export const getFileContent = (fileId: number) =>
  request<{ file_id: number; extract_status: string; text_length: number; preview: string | null; extracted_at: string | null }>(`/files/${fileId}/content`);

// Files
export const getFiles = (params: {
  page?: number;
  page_size?: number;
  extension?: string;
  keyword?: string;
  duplicated?: boolean;
  sort_by?: string;
  sort_order?: string;
}) => {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  if (params.extension) qs.set("extension", params.extension);
  if (params.keyword) qs.set("keyword", params.keyword);
  if (params.duplicated !== undefined) qs.set("duplicated", String(params.duplicated));
  if (params.sort_by) qs.set("sort_by", params.sort_by);
  if (params.sort_order) qs.set("sort_order", params.sort_order);
  return request<import("../types").PaginatedResponse<import("../types").FileRecord>>(`/files?${qs}`);
};

// Duplicates
export const getDuplicates = () =>
  request<{ groups: import("../types").DuplicateGroup[] }>("/duplicates");

export const createDuplicateSuggestions = (sha256: string, filename: string, keepFileId: number) =>
  request<{ created_count: number }>("/duplicates/suggestions", {
    method: "POST",
    body: JSON.stringify({ sha256, filename, keep_file_id: keepFileId }),
  });

// Suggestions
export const generateSuggestions = (archiveRoot: string) =>
  request<{ created_count: number; skipped_count: number }>("/suggestions/generate", {
    method: "POST",
    body: JSON.stringify({ archive_root: archiveRoot }),
  });

export const getSuggestions = (params: { status?: string; page?: number; page_size?: number }) => {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  return request<import("../types").PaginatedResponse<import("../types").FileSuggestion>>(`/suggestions?${qs}`);
};

export const updateSuggestion = (id: number, data: { status?: string; target_path?: string }) =>
  request<import("../types").FileSuggestion>(`/suggestions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const bulkRejectSuggestions = (status: string = "pending") =>
  request<{ status: string; rejected_count: number }>("/suggestions/bulk-reject", {
    method: "POST",
    body: JSON.stringify({ status }),
  });

// Operations
export const executeSuggestions = (suggestionIds: number[]) =>
  request<{ success_count: number; failed_count: number; results: unknown[] }>(
    "/operations/execute-suggestions",
    { method: "POST", body: JSON.stringify({ suggestion_ids: suggestionIds }) },
  );

export const getOperations = (params: { page?: number; page_size?: number }) => {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  return request<import("../types").PaginatedResponse<import("../types").OperationLog>>(`/operations?${qs}`);
};

export const rollbackOperation = (operationId: number) =>
  request<{ operation_id: number; status: string }>(`/operations/${operationId}/rollback`, {
    method: "POST",
  });

// AI Rule Drafts
export const createRuleDraft = (prompt: string) =>
  request<import("../types").RuleDraftResponse>("/ai/rule-drafts", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });

export const previewRuleDraft = (draftId: number) =>
  request<import("../types").PreviewResponse>(`/ai/rule-drafts/${draftId}/preview`);

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


