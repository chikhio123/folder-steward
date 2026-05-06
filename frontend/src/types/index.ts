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
}

export interface DuplicateGroup {
  sha256: string;
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
  status: "pending" | "accepted" | "rejected" | "executed" | "failed";
}

export interface OperationLog {
  id: number;
  operation_type: "move" | "rename" | "rollback";
  source_path: string;
  target_path: string | null;
  status: "success" | "failed" | "rolled_back";
  rollback_available: boolean;
  executed_at: string;
  error_message: string | null;
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

declare global {
  interface Window {
    electronAPI?: {
      openInFolder: (path: string) => void;
      selectDirectory: () => Promise<string | null>;
      onBackendError: (callback: (message: string) => void) => void;
    };
  }
}
