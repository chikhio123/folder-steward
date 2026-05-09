import { request } from './client';

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
  return request<import("../../types").PaginatedResponse<import("../../types").FileSuggestion>>(`/suggestions?${qs}`);
};

export const updateSuggestion = (id: number, data: { status?: string; target_path?: string }) =>
  request<import("../../types").FileSuggestion>(`/suggestions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const bulkRejectSuggestions = (status: string = "pending") =>
  request<{ status: string; rejected_count: number }>("/suggestions/bulk-reject", {
    method: "POST",
    body: JSON.stringify({ status }),
  });
