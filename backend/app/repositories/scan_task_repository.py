from typing import Optional

from ..core.database import get_connection
from ..models.scan_task import ScanTask, ScanError, now_iso


class ScanTaskRepository:
    def create(self, root_path: str) -> ScanTask:
        conn = get_connection()
        now = now_iso()
        cur = conn.execute(
            "INSERT INTO scan_tasks (root_path, status, created_at) VALUES (?, ?, ?)",
            (root_path, "pending", now),
        )
        conn.commit()
        return ScanTask(id=cur.lastrowid, root_path=root_path, status="pending", created_at=now)

    def get(self, task_id: int) -> Optional[ScanTask]:
        row = get_connection().execute(
            "SELECT * FROM scan_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        return ScanTask(**dict(row))

    def update(self, task: ScanTask) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE scan_tasks SET status=?, total_files=?, scanned_files=?,
               failed_files=?, error_message=?, started_at=?, finished_at=?
               WHERE id=?""",
            (task.status, task.total_files, task.scanned_files,
             task.failed_files, task.error_message, task.started_at,
             task.finished_at, task.id),
        )
        conn.commit()

    def list_recent(self, limit: int = 5) -> list[ScanTask]:
        rows = get_connection().execute(
            "SELECT * FROM scan_tasks ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [ScanTask(**dict(r)) for r in rows]


class ScanErrorRepository:
    def create(self, task_id: int, file_path: str, error_message: str) -> ScanError:
        conn = get_connection()
        now = now_iso()
        cur = conn.execute(
            "INSERT INTO scan_errors (task_id, file_path, error_message, created_at) VALUES (?, ?, ?, ?)",
            (task_id, file_path, error_message, now),
        )
        conn.commit()
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
