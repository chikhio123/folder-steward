from typing import Optional
from ..core.database import get_connection

class SearchService:
    def search(
        self,
        query: str,
        scope: str = "all",
        extension: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict], int]:
        if not query.strip():
            return [], 0

        # Safe FTS5 query formatting: wrap in double quotes, escape existing quotes by doubling them
        safe_query = query.replace('"', '""')
        match_expr = f'"{safe_query}"'

        # Modify match_expr based on scope
        if scope == "filename":
            match_expr = f'filename : "{safe_query}"'
        elif scope == "content":
            match_expr = f'text_content : "{safe_query}"'
        # if scope == "all", match_expr searches all columns

        conn = get_connection()
        params = [match_expr]

        where_clauses = ["f.status = 'active'"]
        if extension:
            where_clauses.append("f.extension = ?")
            params.append(extension)

        where_sql = " AND ".join(where_clauses)

        # Count total
        count_sql = f"""
            SELECT COUNT(*) as cnt
            FROM file_content_fts fts
            JOIN file_records f ON fts.file_id = f.id
            WHERE file_content_fts MATCH ? AND {where_sql}
        """
        count_row = conn.execute(count_sql, params).fetchone()
        total = count_row["cnt"] if count_row else 0

        if total == 0:
            return [], 0

        # Query items
        # Use snippet on text_content column (index 3 in FTS5 table: 0=file_id, 1=filename, 2=current_path, 3=text_content)
        # However, if scope is filename, we might want to snippet filename.
        # For simplicity, we just snippet text_content and return it.
        # FTS5 rank is used for scoring.
        offset = (page - 1) * page_size
        params.extend([page_size, offset])

        select_sql = f"""
            SELECT
                f.id as file_id,
                f.filename,
                f.current_path,
                f.extension,
                fts.rank as score,
                snippet(file_content_fts, 3, '<mark>', '</mark>', '...', 32) as snippet
            FROM file_content_fts fts
            JOIN file_records f ON fts.file_id = f.id
            WHERE file_content_fts MATCH ? AND {where_sql}
            ORDER BY fts.rank
            LIMIT ? OFFSET ?
        """

        rows = conn.execute(select_sql, params).fetchall()

        items = []
        for r in rows:
            # Determine match source roughly based on whether snippet is empty or just '...'
            match_source = "content"
            snip = r["snippet"]

            # If the search was restricted to filename, source is filename
            if scope == "filename":
                match_source = "filename"
                snip = None
            elif not snip or snip == "..." or "<mark>" not in snip:
                # If there's no highlight in the text_content snippet, it probably matched filename
                match_source = "filename"
                snip = None

            items.append({
                "file_id": r["file_id"],
                "filename": r["filename"],
                "current_path": r["current_path"],
                "extension": r["extension"],
                "match_source": match_source,
                "snippet": snip,
                "score": r["score"],
            })

        return items, total
