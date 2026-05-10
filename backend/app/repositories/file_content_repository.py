from typing import Optional
from ..core.database import get_connection, require_transaction
from ..models.file_content import FileContent
from ..models.scan_task import now_iso

class FileContentRepository:
    def create(self, content: FileContent) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO file_contents
               (file_id, text_content, text_length, extractor_type, extract_status,
                error_message, extracted_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (content.file_id, content.text_content, content.text_length,
             content.extractor_type, content.extract_status, content.error_message,
             content.extracted_at, content.updated_at),
        )
        conn.commit()
        return cur.lastrowid

    def mark_stale(self, file_id: int) -> None:
        require_transaction()
        conn = get_connection()
        conn.execute(
            """UPDATE file_contents
               SET extract_status = 'stale', updated_at = ?
               WHERE file_id = ? AND extract_status = 'completed'""",
            (now_iso(), file_id),
        )

    def get_by_file_id(self, file_id: int) -> Optional[FileContent]:
        row = get_connection().execute(
            "SELECT * FROM file_contents WHERE file_id = ?", (file_id,)
        ).fetchone()
        if not row:
            return None
        return FileContent(**dict(row))

    def upsert(self, content: FileContent) -> int:
        existing = self.get_by_file_id(content.file_id)
        if existing:
            conn = get_connection()
            conn.execute(
                """UPDATE file_contents SET text_content=?, text_length=?,
                   extractor_type=?, extract_status=?, error_message=?,
                   extracted_at=?, updated_at=?
                   WHERE file_id=?""",
                (content.text_content, content.text_length, content.extractor_type,
                 content.extract_status, content.error_message, content.extracted_at,
                 now_iso(), content.file_id),
            )
            conn.commit()
            return existing.id or 0
        return self.create(content)
