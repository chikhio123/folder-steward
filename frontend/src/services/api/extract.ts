import { request } from './client';

export const forceExtractFile = (fileId: number) =>
  request<{ created_count: number; skipped_count: number }>("/extract-tasks", {
    method: "POST",
    body: JSON.stringify({ file_ids: [fileId], mode: "force" }),
  });
