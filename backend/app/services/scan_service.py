import os
import mimetypes
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..core.errors import ScanError, PathSafetyError
from ..models.file_record import FileRecord
from ..models.scan_task import ScanTask, now_iso
from ..repositories.file_repository import FileRepository
from ..repositories.scan_task_repository import ScanTaskRepository, ScanErrorRepository
from .hash_service import HashService
from .path_safety_service import PathSafetyService


class ScanService:
    def __init__(self) -> None:
        self.task_repo = ScanTaskRepository()
        self.file_repo = FileRepository()
        self.error_repo = ScanErrorRepository()
        self.hash_service = HashService()
        self.safety_service = PathSafetyService()
        self._running_tasks: dict[int, threading.Thread] = {}

    def create_scan_task(self, root_path_str: str) -> ScanTask:
        root_path = Path(root_path_str).resolve()
        self.safety_service.validate_scan_root(root_path)

        task = self.task_repo.create(str(root_path))
        thread = threading.Thread(target=self._run_scan, args=(task.id,), daemon=True)
        self._running_tasks[task.id] = thread
        thread.start()
        return task

    def get_task(self, task_id: int) -> Optional[ScanTask]:
        return self.task_repo.get(task_id)

    def get_errors(self, task_id: int) -> list:
        return self.error_repo.list_by_task(task_id)

    def _run_scan(self, task_id: int) -> None:
        task = self.task_repo.get(task_id)
        if not task:
            return

        root = Path(task.root_path)
        task.status = "running"
        task.started_at = now_iso()
        self.task_repo.update(task)

        # First pass: count total files
        try:
            all_paths = list(root.rglob("*"))
            task.total_files = sum(1 for p in all_paths if p.is_file())
            self.task_repo.update(task)
        except Exception as e:
            task.status = "failed"
            task.error_message = f"Failed to enumerate files: {e}"
            task.finished_at = now_iso()
            self.task_repo.update(task)
            return

        # Second pass: scan each file
        scanned = 0
        failed = 0
        for path in all_paths:
            if not path.is_file():
                continue

            try:
                self._scan_single_file(task_id, task, path, root)
                scanned += 1
            except Exception as e:
                failed += 1
                self.error_repo.create(task_id, str(path), str(e))

            task.scanned_files = scanned
            task.failed_files = failed
            self.task_repo.update(task)

        # Done
        task.status = "completed" if failed == 0 else "completed"
        task.scanned_files = scanned
        task.failed_files = failed
        task.finished_at = now_iso()
        self.task_repo.update(task)

        self._running_tasks.pop(task_id, None)

    def _scan_single_file(self, task_id: int, task: ScanTask, path: Path, root: Path) -> None:
        if self.safety_service.is_system_sensitive_path(path):
            return

        if path.name.startswith(".") and not self._should_scan_hidden():
            return

        stat = path.stat()
        size = stat.st_size
        mime_type, _ = mimetypes.guess_type(str(path))
        ext = path.suffix.lower() if path.suffix else None

        sha256_val: Optional[str] = None
        if size <= 100 * 1024 * 1024:  # 100 MB limit for hashing
            try:
                sha256_val = self.hash_service.calculate_sha256(path)
            except ScanError:
                pass  # hash optional, skip on failure

        rel_path = str(path.relative_to(root) if root in path.parents else path)
        modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
        created_at = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(timespec="seconds")

        record = FileRecord(
            original_path=rel_path,
            current_path=str(path),
            filename=path.name,
            extension=ext,
            mime_type=mime_type,
            size_bytes=size,
            sha256=sha256_val,
            created_at=created_at,
            modified_at=modified_at,
            indexed_at=now_iso(),
            status="active",
        )
        self.file_repo.create(record)

    def _should_scan_hidden(self) -> bool:
        from ..core.config import settings
        return settings.scan_hidden_files
