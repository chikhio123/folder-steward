export interface ScanTask {
  task_id: number;
  root_path: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  total_files: number;
  scanned_files: number;
  failed_files: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface ScanError {
  file_path: string;
  error_message: string;
}

export interface FileRecord {
  id: number;
  filename: string;
  current_path: string;
  extension: string | null;
  size_bytes: number;
  sha256: string | null;
  modified_at: string | null;
  status: string;
  last_error: string | null;
}

export interface DuplicateGroup {
  sha256: string;
  filename: string;
  size_bytes: number;
  count: number;
  files: { id: number; filename: string; current_path: string; modified_at: string | null }[];
}

export interface FileSuggestion {
  id: number;
  file_id: number;
  suggestion_type: "move" | "rename" | "move_duplicate";
  source_path: string;
  target_path: string;
  reason: string | null;
  confidence: number;
  conflict_status: "none" | "target_exists" | "source_missing" | "invalid_target";
  status: "pending" | "accepted" | "rejected" | "executed" | "failed" | "superseded" | "stale" | "in_plan";
  archive_root: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface OperationResult {
  suggestion_id: number;
  status: "success" | "failed" | "skipped";
  operation_id?: number;
  error_message?: string;
}

export interface OperationSkipped {
  file_id: number;
  reason: string;
}

export interface OperationLog {
  id: number;
  operation_type: "move" | "rename" | "rollback";
  file_id: number | null;
  source_path: string;
  target_path: string | null;
  status: "success" | "failed" | "rolled_back" | "pending";
  rollback_available: boolean;
  executed_at: string;
  rollback_at: string | null;
  error_message: string | null;
}

export interface AITask {
  id: number;
  task_type: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled" | "rate_limited";
  input_json: string | null;
  result_ref_type: string | null;
  result_ref_id: number | null;
  total_items: number;
  processed_items: number;
  error_message: string | null;
  retry_count: number;
  estimated_tokens: number;
  actual_tokens: number;
  estimated_cost: number;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface PlanItemPreview {
  item_id: number;
  file_id: number;
  source_path: string;
  target_path: string;
  directory_status: string;
  confidence: number;
  reason: string | null;
}

export interface OrganizePlanPreview {
  plan_id: number;
  title: string;
  status: string;
  groups: Record<string, PlanItemPreview[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

export interface SearchResultItem {
  file_id: number;
  filename: string;
  current_path: string;
  extension: string | null;
  match_source: "filename" | "content";
  snippet: string | null;
  score: number;
}

export interface SearchResponse {
  items: SearchResultItem[];
  total: number;
}

export interface RuleDraftResponse {
  draft_id: number;
  name: string;
  rule_type: string;
  pattern: string;
  target_dir: string;
  action: string;
  priority: number;
  reason: string | null;
  confidence: number;
  status: string;
  validation_error: string | null;
}

export interface PreviewItem {
  file_id: number;
  filename: string;
  current_path: string;
  target_path: string;
  reason: string | null;
}

export interface PreviewResponse {
  draft_id: number;
  matched_count: number;
  items: PreviewItem[];
}

export interface AiTask {
  id: number;
  task_type: "rule_draft" | "classification" | "organize_plan" | "summary" | "feedback_rule";
  status: "pending" | "running" | "completed" | "failed" | "cancelled" | "rate_limited";
  input_json: string | null;
  result_ref_type: string | null;
  result_ref_id: number | null;
  total_items: number;
  processed_items: number;
  error_message: string | null;
  estimated_tokens: number;
  actual_tokens: number;
  estimated_cost: number;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Rule {
  id: number;
  name: string;
  rule_type: string;
  pattern: string;
  target_dir: string;
  action: string;
  priority: number;
  enabled: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface OrganizePlanPreview {
  id: number;
  title: string;
  scope: string;
  status: "draft" | "reviewing" | "accepted" | "rejected" | "converted" | "failed";
  summary_json: string | null;
  created_at: string;
  updated_at: string | null;
  groups?: Record<string, PlanGroupItem[]>;
  uncertain_file_ids?: number[];
}

export interface PlanGroupItem {
  file_ids: number[];
  reason: string | null;
}

export interface FileSummary {
  id: number;
  file_id: number;
  summary: string;
  llm_provider: string | null;
  model_name: string | null;
  source_content_hash: string | null;
  status: "pending" | "running" | "completed" | "stale" | "failed";
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
}

declare global {
  interface Window {
    electronAPI?: {
      openInFolder: (path: string) => void;
      selectDirectory: () => Promise<string | null>;
      onBackendError: (callback: (message: string) => void) => void;
    };
  }
}
