from typing import Optional
from ..core.database import get_connection
from ..models.file_summary import FileSummary

class FileSummaryRepository:
    def create(self, summary: FileSummary) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO file_summaries
               (file_id, summary, llm_provider, model_name, source_content_hash,
                status, error_message, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (summary.file_id, summary.summary, summary.llm_provider, summary.model_name,
             summary.source_content_hash, summary.status, summary.error_message,
             summary.created_at, summary.updated_at),
        )
        conn.commit()
        return cur.lastrowid

    def get_by_file_id(self, file_id: int) -> Optional[FileSummary]:
        row = get_connection().execute(
            "SELECT * FROM file_summaries WHERE file_id = ?", (file_id,)
        ).fetchone()
        if not row:
            return None
        return FileSummary(**dict(row))

    def update(self, summary: FileSummary) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE file_summaries SET
               summary=?, llm_provider=?, model_name=?, source_content_hash=?,
               status=?, error_message=?, updated_at=?
               WHERE id=?""",
            (summary.summary, summary.llm_provider, summary.model_name,
             summary.source_content_hash, summary.status, summary.error_message,
             summary.updated_at, summary.id),
        )
        conn.commit()
