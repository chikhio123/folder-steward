from typing import Optional
from ..core.database import get_connection
from ..models.extract_task import ExtractTask
from ..models.scan_task import now_iso

class ExtractTaskRepository:
    def create(self, task: ExtractTask) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO extract_tasks
               (file_id, status, error_message, started_at, finished_at, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (task.file_id, task.status, task.error_message,
             task.started_at, task.finished_at, task.created_at or now_iso()),
        )
        conn.commit()
        return cur.lastrowid

    def get(self, task_id: int) -> Optional[ExtractTask]:
        row = get_connection().execute(
            "SELECT * FROM extract_tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        return ExtractTask(**dict(row))

    def update(self, task: ExtractTask) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE extract_tasks SET status=?, error_message=?,
               started_at=?, finished_at=? WHERE id=?""",
            (task.status, task.error_message, task.started_at,
             task.finished_at, task.id),
        )
        conn.commit()

    def list_paginated(self, status: Optional[str] = None, page: int = 1, page_size: int = 50) -> tuple[list[ExtractTask], int]:
        conn = get_connection()
        if status:
            row = conn.execute("SELECT COUNT(*) as cnt FROM extract_tasks WHERE status = ?", (status,)).fetchone()
            total = row["cnt"]
            rows = conn.execute(
                "SELECT * FROM extract_tasks WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (status, page_size, (page - 1) * page_size),
            ).fetchall()
        else:
            row = conn.execute("SELECT COUNT(*) as cnt FROM extract_tasks").fetchone()
            total = row["cnt"]
            rows = conn.execute(
                "SELECT * FROM extract_tasks ORDER BY id DESC LIMIT ? OFFSET ?",
                (page_size, (page - 1) * page_size),
            ).fetchall()

        return [ExtractTask(**dict(r)) for r in rows], total
