from typing import Optional

from ..core.database import get_connection, require_transaction
from ..models.file_record import FileRecord


class FileRepository:
    def create(self, record: FileRecord) -> int:
        require_transaction()
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
        require_transaction()
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
            escaped_kw = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            conditions.append("filename LIKE ? ESCAPE '\\'")
            params.append(f"%{escaped_kw}%")
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
        require_transaction()
        conn = get_connection()
        conn.execute(
            "UPDATE file_records SET current_path = ? WHERE id = ?",
            (new_path, file_id),
        )

    def find_duplicate_groups(self) -> list[dict]:
        """Return groups of files sharing the same sha256 and filename."""
        conn = get_connection()
        rows = conn.execute(
            """SELECT sha256, filename, size_bytes, COUNT(*) as cnt
               FROM file_records
               WHERE status='active' AND sha256 IS NOT NULL
                 AND current_path NOT LIKE '%Trash_Duplicates%'
               GROUP BY sha256, filename
               HAVING COUNT(*) > 1
               ORDER BY size_bytes DESC"""
        ).fetchall()
        groups = []
        for r in rows:
            files = conn.execute(
                """SELECT id, filename, current_path, modified_at
                   FROM file_records
                   WHERE sha256 = ? AND filename = ? AND status = 'active'
                     AND current_path NOT LIKE '%Trash_Duplicates%'
                   ORDER BY id""",
                (r["sha256"], r["filename"]),
            ).fetchall()
            groups.append({
                "sha256": r["sha256"],
                "filename": r["filename"],
                "size_bytes": r["size_bytes"],
                "count": r["cnt"],
                "files": [dict(f) for f in files],
            })
        return groups

    def count_duplicate_groups(self) -> int:
        row = get_connection().execute(
            """SELECT COUNT(*) as cnt FROM (
                SELECT sha256, filename FROM file_records
                WHERE status='active' AND sha256 IS NOT NULL
                  AND current_path NOT LIKE '%Trash_Duplicates%'
                GROUP BY sha256, filename HAVING COUNT(*) > 1
            )"""
        ).fetchone()
        return row["cnt"]

    def list_all_with_content(self) -> list[tuple[FileRecord, Optional[dict]]]:
        """Fetch all active file records along with their file_content data using a JOIN to avoid N+1 queries."""
        conn = get_connection()
        rows = conn.execute(
            """SELECT
                   f.*,
                   c.text_content, c.text_length, c.extractor_type, c.extract_status,
                   c.error_message, c.extracted_at, c.updated_at as content_updated_at
               FROM file_records f
               LEFT JOIN file_contents c ON f.id = c.file_id
               WHERE f.status = 'active'"""
        ).fetchall()

        results = []
        for r in rows:
            file_rec = FileRecord(
                id=r["id"],
                original_path=r["original_path"],
                current_path=r["current_path"],
                filename=r["filename"],
                extension=r["extension"],
                mime_type=r["mime_type"],
                size_bytes=r["size_bytes"],
                sha256=r["sha256"],
                created_at=r["created_at"],
                modified_at=r["modified_at"],
                indexed_at=r["indexed_at"],
                status=r["status"],
                last_error=r["last_error"],
            )

            content = None
            if r["extract_status"]:  # If LEFT JOIN matched a content row
                from ..models.file_content import FileContent
                content = FileContent(
                    id=None,  # We don't strictly need content ID here
                    file_id=r["id"],
                    text_content=r["text_content"],
                    text_length=r["text_length"],
                    extractor_type=r["extractor_type"],
                    extract_status=r["extract_status"],
                    error_message=r["error_message"],
                    extracted_at=r["extracted_at"],
                    updated_at=r["content_updated_at"]
                )

            results.append((file_rec, content))

        return results

    def get_paths_by_ids(self, file_ids: list[int]) -> list[dict]:
        if not file_ids:
            return []
        conn = get_connection()
        rows = []
        chunk_size = 900
        for i in range(0, len(file_ids), chunk_size):
            chunk = file_ids[i:i + chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            rows.extend(
                conn.execute(
                    f"SELECT id, current_path FROM file_records WHERE id IN ({placeholders})",
                    chunk,
                ).fetchall()
            )
        return [dict(r) for r in rows]

    def get_active_excluding_prefix(self, prefix: str) -> list[int]:
        conn = get_connection()
        from pathlib import Path
        
        def is_inside(path_str: str, root_str: str) -> bool:
            try:
                p = Path(path_str).resolve()
                r = Path(root_str).resolve()
                p.relative_to(r)
                return True
            except ValueError:
                return False

        all_rows = conn.execute("SELECT id, current_path FROM file_records WHERE status = 'active'").fetchall()
        return [
            r["id"]
            for r in all_rows
            if r["current_path"] and not is_inside(r["current_path"], prefix)
        ]

    def get_all_active_ids(self) -> list[int]:
        conn = get_connection()
        rows = conn.execute("SELECT id FROM file_records WHERE status = 'active'").fetchall()
        return [r["id"] for r in rows]
