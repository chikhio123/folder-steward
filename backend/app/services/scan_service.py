import os
import mimetypes
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..core.errors import ScanError, PathSafetyError
from ..core.uow import UnitOfWork
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
        from ..repositories.file_content_repository import FileContentRepository
        self.content_repo = FileContentRepository()
        self._running_tasks: dict[int, threading.Thread] = {}
        self._cancelled_tasks: set[int] = set()

    def create_scan_task(self, root_path_str: str) -> ScanTask:
        root_path = Path(root_path_str).resolve()
        self.safety_service.validate_scan_root(root_path)

        with UnitOfWork():
            task = self.task_repo.create(str(root_path))
        thread = threading.Thread(target=self._run_scan, args=(task.id,), daemon=True)
        self._running_tasks[task.id] = thread
        thread.start()
        return task

    def cancel_task(self, task_id: int) -> bool:
        task = self.task_repo.get(task_id)
        if not task or task.status not in ("pending", "running"):
            return False
        self._cancelled_tasks.add(task_id)
        task.status = "cancelled"
        task.finished_at = now_iso()
        with UnitOfWork():
            self.task_repo.update(task)
        return True

    def _is_cancelled(self, task_id: int) -> bool:
        if task_id in self._cancelled_tasks:
            return True
        task = self.task_repo.get(task_id)
        return bool(task and task.status == "cancelled")

    def _finish_cancelled(self, task: ScanTask) -> None:
        self._cancelled_tasks.discard(task.id)
        latest_task = self.task_repo.get(task.id)
        if latest_task:
            latest_task.status = "cancelled"
            latest_task.finished_at = now_iso()
            with UnitOfWork():
                self.task_repo.update(latest_task)
        self._running_tasks.pop(task.id, None)

    def get_task(self, task_id: int) -> Optional[ScanTask]:
        return self.task_repo.get(task_id)

    def get_errors(self, task_id: int) -> list:
        return self.error_repo.list_by_task(task_id)


    def _cleanup_missing_files(self, root: Path) -> int:
        """Check active files under root and mark as deleted if missing from disk."""
        from ..core.database import get_connection
        conn = get_connection()
        rows = conn.execute("SELECT id, current_path FROM file_records WHERE status = 'active'").fetchall()
        
        root_res = root.resolve()
        deleted_ids = []
        for r in rows:
            path_str = r["current_path"]
            try:
                Path(path_str).resolve().relative_to(root_res)
                if not Path(path_str).exists():
                    deleted_ids.append(r["id"])
            except ValueError:
                pass
                    
        if deleted_ids:
            # Batch update in chunks of 500 to avoid sqlite limits
            chunk_size = 500
            for i in range(0, len(deleted_ids), chunk_size):
                chunk = deleted_ids[i:i+chunk_size]
                placeholders = ",".join("?" for _ in chunk)
                with UnitOfWork():
                    conn = get_connection()
                    conn.execute(f"UPDATE file_records SET status = 'deleted' WHERE id IN ({placeholders})", chunk)
            # We removed conn.commit() here because UnitOfWork handles it per chunk

            # Also clean up FTS for deleted files using triggers we added
        return len(deleted_ids)

    def _run_scan(self, task_id: int) -> None:
        task = self.task_repo.get(task_id)
        if not task:
            return

        root = Path(task.root_path)
        if task.status == "cancelled":
            self._running_tasks.pop(task_id, None)
            return
        task.started_at = now_iso()
        if task.status == "pending":
            with UnitOfWork():
                marked = self.task_repo.mark_running_if_pending(task.id, task.started_at)
            if not marked:
                task = self.task_repo.get(task_id)
                if task and task.status == "cancelled":
                    self._running_tasks.pop(task_id, None)
                    return
                if not task:
                    self._running_tasks.pop(task_id, None)
                    return
        elif task.status != "running":
            self._running_tasks.pop(task_id, None)
            return

        # Single pass: stream through files without holding all paths in memory
        scanned = 0
        failed = 0
        try:
            for path in root.rglob("*"):
                if self._is_cancelled(task_id):
                    self._finish_cancelled(task)
                    return
                if not path.is_file():
                    continue

                try:
                    self._scan_single_file(task_id, task, path, root)
                    scanned += 1
                except Exception as e:
                    failed += 1
                    with UnitOfWork():
                        self.error_repo.create(task_id, str(path), str(e))

                with UnitOfWork():
                    self.task_repo.update_progress(task.id, scanned, failed)
        except Exception as e:
            if self._is_cancelled(task_id):
                self._finish_cancelled(task)
                return
            task.status = "failed"
            task.error_message = f"Scan failed: {e}"
            task.finished_at = now_iso()
            with UnitOfWork():
                self.task_repo.fail_if_running(task)
            self._running_tasks.pop(task_id, None)
            return

        # Done — check cancelled before overwriting status
        if self._is_cancelled(task_id):
            self._finish_cancelled(task)
            return

        # Cleanup missing files (e.g. deleted from file explorer)
        cleaned = self._cleanup_missing_files(root)

        task.status = "completed"
        task.total_files = scanned + failed
        task.scanned_files = scanned
        task.failed_files = failed
        task.error_message = f"Cleaned {cleaned} missing files." if cleaned > 0 else None
        task.finished_at = now_iso()
        with UnitOfWork():
            self.task_repo.complete_if_running(task)

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

        from ..core.config import settings
        sha256_val: Optional[str] = None
        if size <= settings.max_file_size_for_hash:
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

        # Check if file changed to mark stale
        with UnitOfWork():
            existing = self.file_repo.find_by_current_path(record.current_path)
            if existing:
                if existing.modified_at != record.modified_at or existing.size_bytes != record.size_bytes or existing.sha256 != record.sha256:
                    self.content_repo.mark_stale(existing.id)

            self.file_repo.upsert(record)

    def _should_scan_hidden(self) -> bool:
        from ..core.config import settings
        return settings.scan_hidden_files
