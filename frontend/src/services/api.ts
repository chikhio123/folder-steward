import { request } from './api/client';

export * from './api/client';
export * from './api/system';
export * from './api/files';
export * from './api/ai';

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

// Duplicates
export const getDuplicates = () =>
  request<{ groups: import("../types").DuplicateGroup[] }>("/duplicates");

export const isolateDuplicates = (mode: "auto" | "manual", groups?: { sha256: string; keep_file_id?: number }[]) =>
  request<{ success_count: number; failed_count: number; results: any[]; skipped: any[] }>("/duplicates/isolation-plan", {
    method: "POST",
    body: JSON.stringify({ mode, groups }),
  });

// Suggestions
export const generateSuggestions = (archiveRoot: string) =>
  request<{ created_count: number; skipped_count: number }>("/suggestions/generate", {
    method: "POST",
    body: JSON.stringify({ archive_root: archiveRoot }),
  });

export const getSuggestions = (params: { status?: string; page?: number; page_size?: number }) => {
  const qs = new URLSearchParams();
  if (params.status && params.status !== "all") qs.set("status", params.status);
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


