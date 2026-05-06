import threading
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
        self._cleanup_ghost_tasks()

    def _cleanup_ghost_tasks(self) -> None:
        """Reset any 'running' tasks from a previous crashed run back to 'failed'."""
        conn = get_connection()
        conn.execute(
            "UPDATE extract_tasks SET status = 'failed', error_message = 'Process terminated unexpectedly', finished_at = ? WHERE status = 'running'",
            (now_iso(),)
        )
        conn.execute(
            "UPDATE file_contents SET extract_status = 'failed', error_message = 'Process terminated unexpectedly', updated_at = ? WHERE extract_status = 'running'",
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

        query = f"SELECT id, extension FROM file_records WHERE status = 'active' AND extension IN ({placeholders})"

        if file_ids:
            id_placeholders = ",".join("?" * len(file_ids))
            query += f" AND id IN ({id_placeholders})"
            params.extend(file_ids)

        records = conn.execute(query, params).fetchall()

        created = 0
        skipped = 0

        for r in records:
            file_id = r["id"]

            content = self.content_repo.get_by_file_id(file_id)

            # Prevent duplicate pending/running tasks
            if content and content.extract_status in ("pending", "running"):
                skipped += 1
                continue

            if mode == "missing_only":
                if content and content.extract_status == "completed":
                    skipped += 1
                    continue
            elif mode == "failed_only":
                if not content or content.extract_status != "failed":
                    skipped += 1
                    continue

            # Upsert pending state into file_contents immediately so frontend UI updates
            pending_content = FileContent(
                file_id=file_id,
                extractor_type=content.extractor_type if content else "unknown",
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

        try:
            result = extractor.extract(path)

            content = FileContent(
                file_id=file_record.id,
                text_content=result.text,
                text_length=len(result.text),
                extractor_type=extractor.__class__.__name__,
                extract_status="completed",
                error_message="; ".join(result.warnings) if result.warnings else None,
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
