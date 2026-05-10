from typing import Optional

from ..core.database import get_connection, require_transaction
from ..models.scan_task import ScanTask, ScanError, now_iso


class ScanTaskRepository:
    def create(self, root_path: str) -> ScanTask:
        require_transaction()
        conn = get_connection()
        now = now_iso()
        cur = conn.execute(
            "INSERT INTO scan_tasks (root_path, status, created_at) VALUES (?, ?, ?)",
            (root_path, "pending", now),
        )
        return ScanTask(id=cur.lastrowid, root_path=root_path, status="pending", created_at=now)

    def get(self, task_id: int) -> Optional[ScanTask]:
        row = get_connection().execute(
            "SELECT * FROM scan_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        return ScanTask(**dict(row))

    def update(self, task: ScanTask) -> None:
        require_transaction()
        conn = get_connection()
        conn.execute(
            """UPDATE scan_tasks SET status=?, total_files=?, scanned_files=?,
               failed_files=?, error_message=?, started_at=?, finished_at=?
               WHERE id=?""",
            (task.status, task.total_files, task.scanned_files,
             task.failed_files, task.error_message, task.started_at,
             task.finished_at, task.id),
        )

    def mark_running_if_pending(self, task_id: int, started_at: str) -> bool:
        require_transaction()
        conn = get_connection()
        cur = conn.execute(
            "UPDATE scan_tasks SET status='running', started_at=? WHERE id=? AND status='pending'",
            (started_at, task_id),
        )
        return cur.rowcount == 1

    def update_progress(self, task_id: int, scanned: int, failed: int) -> None:
        """Update only progress counters without touching status/state fields.
        Prevents race conditions where cancel_task sets cancelled but
        the scan loop's periodic update overwrites it back to running."""
        require_transaction()
        conn = get_connection()
        conn.execute(
            "UPDATE scan_tasks SET scanned_files=?, failed_files=? WHERE id=?",
            (scanned, failed, task_id),
        )

    def complete_if_running(self, task: ScanTask) -> bool:
        require_transaction()
        conn = get_connection()
        cur = conn.execute(
            """UPDATE scan_tasks SET status=?, total_files=?, scanned_files=?,
               failed_files=?, error_message=?, finished_at=?
               WHERE id=? AND status='running'""",
            (task.status, task.total_files, task.scanned_files,
             task.failed_files, task.error_message, task.finished_at, task.id),
        )
        return cur.rowcount == 1

    def fail_if_running(self, task: ScanTask) -> bool:
        require_transaction()
        conn = get_connection()
        cur = conn.execute(
            """UPDATE scan_tasks SET status='failed', error_message=?, finished_at=?
               WHERE id=? AND status='running'""",
            (task.error_message, task.finished_at, task.id),
        )
        return cur.rowcount == 1

    def list_recent(self, limit: int = 5) -> list[ScanTask]:
        rows = get_connection().execute(
            "SELECT * FROM scan_tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [ScanTask(**dict(r)) for r in rows]


class ScanErrorRepository:
    def create(self, task_id: int, file_path: str, error_message: str) -> ScanError:
        require_transaction()
        conn = get_connection()
        now = now_iso()
        cur = conn.execute(
            "INSERT INTO scan_errors (task_id, file_path, error_message, created_at) VALUES (?, ?, ?, ?)",
            (task_id, file_path, error_message, now),
        )
        return ScanError(id=cur.lastrowid, task_id=task_id, file_path=file_path,
                         error_message=error_message, created_at=now)

    def list_by_task(self, task_id: int) -> list[ScanError]:
        rows = get_connection().execute(
            "SELECT * FROM scan_errors WHERE task_id = ? ORDER BY id", (task_id,)
        ).fetchall()
        return [ScanError(**dict(r)) for r in rows]

    def count_by_task(self, task_id: int) -> int:
        row = get_connection().execute(
            "SELECT COUNT(*) as cnt FROM scan_errors WHERE task_id = ?", (task_id,)
        ).fetchone()
        return row["cnt"] if row else 0
