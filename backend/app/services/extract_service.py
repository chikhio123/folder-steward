from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from pathlib import Path

from ..core.database import get_connection
from ..models.extract_task import ExtractTask
from ..models.file_content import FileContent
from ..models.scan_task import now_iso
from ..repositories.extract_task_repository import ExtractTaskRepository
from ..repositories.file_repository import FileRepository
from ..repositories.file_content_repository import FileContentRepository
from .text_extractors import get_extractor

class ExtractService:
    _executor = ThreadPoolExecutor(max_workers=8)

    def __init__(self) -> None:
        self.task_repo = ExtractTaskRepository()
        self.file_repo = FileRepository()
        self.content_repo = FileContentRepository()

    @staticmethod
    def cleanup_ghost_tasks() -> None:
        """Reset any 'running' or 'pending' tasks from a previous crashed run back to 'failed'."""
        conn = get_connection()
        conn.execute(
            "UPDATE extract_tasks SET status = 'failed', error_message = 'Process terminated unexpectedly', finished_at = ? WHERE status IN ('running', 'pending')",
            (now_iso(),)
        )
        conn.execute(
            "UPDATE file_contents SET extract_status = 'failed', error_message = 'Process terminated unexpectedly', updated_at = ? WHERE extract_status IN ('running', 'pending')",
            (now_iso(),)
        )
        conn.commit()

    def create_extract_tasks(self, file_ids: Optional[list[int]] = None, mode: str = "missing_only") -> tuple[int, int]:
        conn = get_connection()

        # 确定支持的扩展名
        from .text_extractors import _EXTRACTORS
        supported_exts = set()
        for ex in _EXTRACTORS:
            supported_exts.update(ex.supported_extensions)
        placeholders = ",".join("?" * len(supported_exts))

        params = list(supported_exts)

        # Base query using LEFT JOIN to get content status directly
        query = f"""
            SELECT f.id, c.extract_status, c.extractor_type
            FROM file_records f
            LEFT JOIN file_contents c ON f.id = c.file_id
            WHERE f.status = 'active' AND f.extension IN ({placeholders})
        """

        # Filter by file_ids if provided
        if file_ids:
            id_placeholders = ",".join("?" * len(file_ids))
            query += f" AND f.id IN ({id_placeholders})"
            params.extend(file_ids)

        # Add condition based on mode directly into SQL to eliminate Python-side filtering
        if mode == "missing_only":
            query += " AND (c.extract_status IS NULL OR c.extract_status NOT IN ('pending', 'running', 'completed'))"
        elif mode == "failed_only":
            query += " AND c.extract_status = 'failed'"
        elif mode == "stale_only":
            query += " AND c.extract_status = 'stale'"
        elif mode == "rebuild_all":
            # rebuild_all covers missing, failed, and stale.
            query += " AND (c.extract_status IS NULL OR c.extract_status IN ('failed', 'stale') OR c.extract_status NOT IN ('pending', 'running', 'completed'))"
        elif mode == "force":
            # force bypasses completed checks but should still avoid duplicate pending/running
            query += " AND (c.extract_status IS NULL OR c.extract_status NOT IN ('pending', 'running'))"

        records = conn.execute(query, params).fetchall()

        created = 0
        skipped = 0 # With SQL filtering, skipped is mostly 0 since we only select actionable rows, but keeping the var for return signature

        for r in records:
            file_id = r["id"]

            # Upsert pending state into file_contents immediately so frontend UI updates
            pending_content = FileContent(
                file_id=file_id,
                extractor_type=r["extractor_type"] if r["extractor_type"] else "unknown",
                extract_status="pending",
                error_message=None
            )
            self.content_repo.upsert(pending_content)

            task = ExtractTask(
                file_id=file_id,
                status="pending",
                created_at=now_iso()
            )
            task_id = self.task_repo.create(task)
            created += 1

            # Dispatch execution in thread pool
            self._executor.submit(self.run_extract_task, task_id)

        return created, skipped

    def run_extract_task(self, task_id: int) -> None:
        task = self.task_repo.get(task_id)
        if not task or task.status != "pending":
            return

        task.status = "running"
        task.started_at = now_iso()
        self.task_repo.update(task)

        content = self.content_repo.get_by_file_id(task.file_id)
        if content:
            content.extract_status = "running"
            self.content_repo.upsert(content)

        file_record = self.file_repo.get(task.file_id)
        if not file_record or file_record.status != "active":
            self._fail_task(task, "File record not found or inactive")
            return

        extractor = get_extractor(file_record.extension)
        if not extractor:
            self._skip_task(task, "Unsupported file extension")
            return

        path = Path(file_record.current_path)
        if not path.exists():
            self._fail_task(task, "File not found on disk")
            return

        if not path.is_file():
            self._fail_task(task, "Path is not a regular file")
            return

        from .extract_limits import MAX_EXTRACT_FILE_MB, MAX_TEXT_CHARS
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > MAX_EXTRACT_FILE_MB:
                self._fail_task(task, f"File size {size_mb:.2f}MB exceeds limit of {MAX_EXTRACT_FILE_MB}MB")
                return
        except Exception as e:
            self._fail_task(task, f"Failed to read file size: {e}")
            return

        try:
            result = extractor.extract(path)

            text = result.text
            warnings = list(result.warnings or [])

            if len(text) > MAX_TEXT_CHARS:
                text = text[:MAX_TEXT_CHARS]
                warnings.append(f"Text truncated to {MAX_TEXT_CHARS} characters")

            content = FileContent(
                file_id=file_record.id,
                text_content=text,
                text_length=len(text),
                extractor_type=extractor.__class__.__name__,
                extract_status="completed",
                error_message="; ".join(warnings) if warnings else None,
                extracted_at=now_iso(),
            )
            self.content_repo.upsert(content)

            task.status = "completed"
            task.finished_at = now_iso()
            self.task_repo.update(task)

        except Exception as e:
            self._fail_task(task, str(e))

    def _fail_task(self, task: ExtractTask, error: str) -> None:
        task.status = "failed"
        task.error_message = error
        task.finished_at = now_iso()
        self.task_repo.update(task)

        content = FileContent(
            file_id=task.file_id,
            extractor_type="unknown",
            extract_status="failed",
            error_message=error,
        )
        self.content_repo.upsert(content)

    def _skip_task(self, task: ExtractTask, reason: str) -> None:
        task.status = "skipped"
        task.error_message = reason
        task.finished_at = now_iso()
        self.task_repo.update(task)

        content = FileContent(
            file_id=task.file_id,
            extractor_type="unknown",
            extract_status="skipped",
            error_message=reason,
        )
        self.content_repo.upsert(content)
