from typing import Optional

from ..core.database import get_connection
from ..models.file_record import FileRecord


class FileRepository:
    def create(self, record: FileRecord) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO file_records
               (original_path, current_path, filename, extension, mime_type,
                size_bytes, sha256, created_at, modified_at, indexed_at, status, last_error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record.original_path, record.current_path, record.filename,
             record.extension, record.mime_type, record.size_bytes,
             record.sha256, record.created_at, record.modified_at,
             record.indexed_at, record.status, record.last_error),
        )
        conn.commit()
        return cur.lastrowid

    def find_by_current_path(self, current_path: str) -> Optional[FileRecord]:
        row = get_connection().execute(
            "SELECT * FROM file_records WHERE current_path = ?", (current_path,)
        ).fetchone()
        if not row:
            return None
        return FileRecord(**dict(row))

    def upsert(self, record: FileRecord) -> int:
        """Insert if new, update if existing by current_path. Returns record id."""
        existing = self.find_by_current_path(record.current_path)
        if existing:
            conn = get_connection()
            conn.execute(
                """UPDATE file_records SET original_path=?, filename=?, extension=?,
                   mime_type=?, size_bytes=?, sha256=?, modified_at=?,
                   indexed_at=?, status=?, last_error=?
                   WHERE id=?""",
                (record.original_path, record.filename, record.extension,
                 record.mime_type, record.size_bytes, record.sha256,
                 record.modified_at, record.indexed_at, record.status,
                 record.last_error, existing.id),
            )
            conn.commit()
            return existing.id
        return self.create(record)

    def get(self, file_id: int) -> Optional[FileRecord]:
        row = get_connection().execute(
            "SELECT * FROM file_records WHERE id = ?", (file_id,)
        ).fetchone()
        if not row:
            return None
        return FileRecord(**dict(row))

    def count(self) -> int:
        row = get_connection().execute("SELECT COUNT(*) as cnt FROM file_records WHERE status='active'").fetchone()
        return row["cnt"]

    def total_size(self) -> int:
        row = get_connection().execute("SELECT COALESCE(SUM(size_bytes), 0) as total FROM file_records WHERE status='active'").fetchone()
        return row["total"]

    def list_paginated(
        self,
        page: int = 1,
        page_size: int = 50,
        extension: Optional[str] = None,
        keyword: Optional[str] = None,
        duplicated: Optional[bool] = None,
        sort_by: str = "modified_at",
        sort_order: str = "desc",
    ) -> tuple[list[FileRecord], int]:
        conn = get_connection()
        conditions = ["status = 'active'"]
        params: list = []

        if extension:
            conditions.append("extension = ?")
            params.append(extension)
        if keyword:
            conditions.append("id IN (SELECT file_id FROM file_content_fts WHERE file_content_fts MATCH ?)")
            # quote the keyword to avoid FTS syntax errors for special chars
            safe_keyword = keyword.replace('"', '""')
            params.append(f'"{safe_keyword}"')
        if duplicated is True:
            conditions.append("sha256 IN (SELECT sha256 FROM file_records WHERE status='active' GROUP BY sha256 HAVING COUNT(*) > 1)")
        elif duplicated is False:
            conditions.append("sha256 IN (SELECT sha256 FROM file_records WHERE status='active' GROUP BY sha256 HAVING COUNT(*) = 1)")

        where = " AND ".join(conditions)

        allowed_sort = {"modified_at", "size_bytes", "filename", "created_at"}
        if sort_by not in allowed_sort:
            sort_by = "modified_at"
        order = "ASC" if sort_order.upper() == "ASC" else "DESC"

        count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM file_records WHERE {where}", params).fetchone()
        total = count_row["cnt"]

        offset = (page - 1) * page_size
        rows = conn.execute(
            f"SELECT * FROM file_records WHERE {where} ORDER BY {sort_by} {order} LIMIT ? OFFSET ?",
            [*params, page_size, offset],
        ).fetchall()

        return [FileRecord(**dict(r)) for r in rows], total

    def update_path(self, file_id: int, new_path: str) -> None:
        conn = get_connection()
        conn.execute(
            "UPDATE file_records SET current_path = ? WHERE id = ?",
            (new_path, file_id),
        )
        conn.commit()

    def find_duplicate_groups(self) -> list[dict]:
        """Return groups of files sharing the same sha256 (and non-null)."""
        conn = get_connection()
        rows = conn.execute(
            """SELECT sha256, size_bytes, COUNT(*) as cnt
               FROM file_records
               WHERE status='active' AND sha256 IS NOT NULL
               GROUP BY sha256
               HAVING COUNT(*) > 1
               ORDER BY size_bytes DESC"""
        ).fetchall()
        groups = []
        for r in rows:
            files = conn.execute(
                "SELECT id, filename, current_path, modified_at FROM file_records WHERE sha256 = ? ORDER BY id",
                (r["sha256"],),
            ).fetchall()
            groups.append({
                "sha256": r["sha256"],
                "size_bytes": r["size_bytes"],
                "count": r["cnt"],
                "files": [dict(f) for f in files],
            })
        return groups

    def count_duplicate_groups(self) -> int:
        row = get_connection().execute(
            """SELECT COUNT(*) as cnt FROM (
                SELECT sha256 FROM file_records
                WHERE status='active' AND sha256 IS NOT NULL
                GROUP BY sha256 HAVING COUNT(*) > 1
            )"""
        ).fetchone()
        return row["cnt"]
