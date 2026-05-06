const BASE_URL = "/api";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || res.statusText);
  }
  return res.json();
}

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

export const createDuplicateSuggestions = (sha256: string, keepFileId: number) =>
  request<{ created_count: number }>("/duplicates/suggestions", {
    method: "POST",
    body: JSON.stringify({ sha256, keep_file_id: keepFileId }),
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

// Settings
export const getSettings = () => request<Record<string, string>>("/settings");

export const updateSettings = (settings: Record<string, string>) =>
  request<Record<string, string>>("/settings", {
    method: "PUT",
    body: JSON.stringify(settings),
  });

// Search
export const searchFiles = (params: { q: string; scope?: string; extension?: string; page?: number; page_size?: number }) => {
  const qs = new URLSearchParams();
  qs.set("q", params.q);
  if (params.scope) qs.set("scope", params.scope);
  if (params.extension) qs.set("extension", params.extension);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  return request<import("../types").SearchResponse>(`/search?${qs}`);
};

export const rebuildSearchIndex = () =>
  request<{ indexed_count: number; failed_count: number }>("/search/rebuild-index", { method: "POST" });

// Dashboard
export const getDashboard = () =>
  request<{
    total_files: number;
    total_size: number;
    duplicate_groups: number;
    pending_suggestions: number;
    recent_tasks: import("../types").ScanTask[];
    recent_operations: import("../types").OperationLog[];
  }>("/dashboard");
