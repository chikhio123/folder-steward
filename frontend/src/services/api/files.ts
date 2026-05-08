import { request } from './client';

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
  return request<import("../../types").PaginatedResponse<import("../../types").FileRecord>>(`/files?${qs}`);
};
