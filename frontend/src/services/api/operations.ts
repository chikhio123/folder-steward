import { request } from './client';

export const executeSuggestions = (suggestionIds: number[]) =>
  request<{ success_count: number; failed_count: number; results: unknown[] }>(
    "/operations/execute-suggestions",
    { method: "POST", body: JSON.stringify({ suggestion_ids: suggestionIds }) },
  );

export const getOperations = (params: { page?: number; page_size?: number }) => {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  return request<import("../../types").PaginatedResponse<import("../../types").OperationLog>>(`/operations?${qs}`);
};

export const rollbackOperation = (operationId: number) =>
  request<{ operation_id: number; status: string }>(`/operations/${operationId}/rollback`, {
    method: "POST",
  });
