import { request } from './client';
import type { SearchResponse } from '../../types';

export const getSettings = () => request<Record<string, string>>('/settings');

export const updateSettings = (settings: Record<string, string>) =>
  request<Record<string, string>>('/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });

export const searchFiles = (params: { q: string; scope?: string; extension?: string; page?: number; page_size?: number }) => {
  const qs = new URLSearchParams();
  qs.set("q", params.q);
  if (params.scope) qs.set("scope", params.scope);
  if (params.extension) qs.set("extension", params.extension);
  if (params.page) qs.set("page", String(params.page));
  if (params.page_size) qs.set("page_size", String(params.page_size));
  return request<SearchResponse>(`/search?${qs}`);
};

export const getDashboard = () =>
  request<{
    total_files: number;
    total_size: number;
    duplicate_groups: number;
    pending_suggestions: number;
    recent_tasks: import("../../types").ScanTask[];
    recent_operations: import("../../types").OperationLog[];
  }>("/dashboard");

export const rebuildSearchIndex = () =>
  request<{ indexed_count: number; failed_count: number }>("/search/rebuild-index", { method: "POST" });

export const getAvailableModels = (baseUrl: string, apiKey: string) => {
  const qs = new URLSearchParams();
  qs.set("base_url", baseUrl);
  qs.set("api_key", apiKey);
  return request<{ models: string[] }>(`/settings/models?${qs}`);
};

