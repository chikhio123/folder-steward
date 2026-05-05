from typing import Optional

from ..core.database import get_connection
from ..models.operation_log import OperationLog


class OperationLogRepository:
    def create(self, log: OperationLog) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO operation_logs
               (operation_type, file_id, source_path, target_path, status,
                rollback_available, executed_at, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (log.operation_type, log.file_id, log.source_path, log.target_path,
             log.status, log.rollback_available, log.executed_at, log.error_message),
        )
        conn.commit()
        return cur.lastrowid

    def get(self, operation_id: int) -> Optional[OperationLog]:
        row = get_connection().execute(
            "SELECT * FROM operation_logs WHERE id = ?", (operation_id,)
        ).fetchone()
        if not row:
            return None
        return OperationLog(**dict(row))

    def update(self, log: OperationLog) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE operation_logs SET status=?, rollback_available=?, rollback_at=?,
               error_message=? WHERE id=?""",
            (log.status, log.rollback_available, log.rollback_at,
             log.error_message, log.id),
        )
        conn.commit()

    def list_paginated(self, page: int = 1, page_size: int = 50) -> tuple[list[OperationLog], int]:
        conn = get_connection()
        row = conn.execute("SELECT COUNT(*) as cnt FROM operation_logs").fetchone()
        total = row["cnt"]
        rows = conn.execute(
            "SELECT * FROM operation_logs ORDER BY executed_at DESC LIMIT ? OFFSET ?",
            (page_size, (page - 1) * page_size),
        ).fetchall()
        return [OperationLog(**dict(r)) for r in rows], total

    def list_recent(self, limit: int = 5) -> list[OperationLog]:
        rows = get_connection().execute(
            "SELECT * FROM operation_logs ORDER BY executed_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [OperationLog(**dict(r)) for r in rows]
