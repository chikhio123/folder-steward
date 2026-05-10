import { request } from './client';

export const getDuplicates = () =>
  request<{ groups: import("../../types").DuplicateGroup[] }>("/duplicates");

export const isolateDuplicates = (mode: "auto" | "manual", groups?: { sha256: string; filename?: string; keep_file_id?: number }[], isolation_strategy: "local" | "global" = "local") =>
  request<{ success_count: number; failed_count: number; results: import("../../types").OperationResult[]; skipped: import("../../types").OperationSkipped[] }>("/duplicates/isolation-plan", {
    method: "POST",
    body: JSON.stringify({ mode, groups, isolation_strategy }),
  });
