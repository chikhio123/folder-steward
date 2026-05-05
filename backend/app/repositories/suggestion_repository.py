from typing import Optional

from ..core.database import get_connection
from ..models.file_suggestion import FileSuggestion
from ..models.scan_task import now_iso


class SuggestionRepository:
    def create(self, suggestion: FileSuggestion) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO file_suggestions
               (file_id, suggestion_type, source_path, target_path, reason,
                confidence, conflict_status, status, archive_root, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (suggestion.file_id, suggestion.suggestion_type, suggestion.source_path,
             suggestion.target_path, suggestion.reason, suggestion.confidence,
             suggestion.conflict_status, suggestion.status, suggestion.archive_root,
             suggestion.created_at),
        )
        conn.commit()
        return cur.lastrowid

    def get(self, suggestion_id: int) -> Optional[FileSuggestion]:
        row = get_connection().execute(
            "SELECT * FROM file_suggestions WHERE id = ?", (suggestion_id,)
        ).fetchone()
        if not row:
            return None
        return FileSuggestion(**dict(row))

    def update(self, suggestion: FileSuggestion) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE file_suggestions SET status=?, target_path=?, conflict_status=?, archive_root=?,
               updated_at=? WHERE id=?""",
            (suggestion.status, suggestion.target_path, suggestion.conflict_status,
             suggestion.archive_root, now_iso(), suggestion.id),
        )
        conn.commit()

    def update_status(self, suggestion_id: int, status: str) -> None:
        conn = get_connection()
        conn.execute(
            "UPDATE file_suggestions SET status=?, updated_at=? WHERE id=?",
            (status, now_iso(), suggestion_id),
        )
        conn.commit()

    def list_paginated(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[FileSuggestion], int]:
        conn = get_connection()
        if status:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM file_suggestions WHERE status = ?", (status,)
            ).fetchone()
            total = row["cnt"]
            rows = conn.execute(
                "SELECT * FROM file_suggestions WHERE status = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (status, page_size, (page - 1) * page_size),
            ).fetchall()
        else:
            row = conn.execute("SELECT COUNT(*) as cnt FROM file_suggestions").fetchone()
            total = row["cnt"]
            rows = conn.execute(
                "SELECT * FROM file_suggestions ORDER BY id DESC LIMIT ? OFFSET ?",
                (page_size, (page - 1) * page_size),
            ).fetchall()

        return [FileSuggestion(**dict(r)) for r in rows], total

    def list_by_ids(self, ids: list[int]) -> list[FileSuggestion]:
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        rows = get_connection().execute(
            f"SELECT * FROM file_suggestions WHERE id IN ({placeholders})", ids
        ).fetchall()
        return [FileSuggestion(**dict(r)) for r in rows]

    def count_pending(self) -> int:
        row = get_connection().execute(
            "SELECT COUNT(*) as cnt FROM file_suggestions WHERE status='pending'"
        ).fetchone()
        return row["cnt"]

    def mark_superseded_for_file(self, file_id: int) -> None:
        conn = get_connection()
        conn.execute(
            "UPDATE file_suggestions SET status='superseded', updated_at=? WHERE file_id=? AND status='pending'",
            (now_iso(), file_id),
        )
        conn.commit()

    def delete_by_file_id(self, file_id: int) -> None:
        get_connection().execute(
            "DELETE FROM file_suggestions WHERE file_id = ?", (file_id,)
        )
        get_connection().commit()
