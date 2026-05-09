import { request } from './client';

export const getDuplicates = () =>
  request<{ groups: import("../../types").DuplicateGroup[] }>("/duplicates");

export const isolateDuplicates = (mode: "auto" | "manual", groups?: { sha256: string; filename?: string; keep_file_id?: number }[]) =>
  request<{ success_count: number; failed_count: number; results: any[]; skipped: any[] }>("/duplicates/isolation-plan", {
    method: "POST",
    body: JSON.stringify({ mode, groups }),
  });
