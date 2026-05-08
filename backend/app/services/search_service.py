import html
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

        # Relax exact phrase matching: split by spaces and wrap each word in quotes
        words = [w.replace('"', '""') for w in query.split() if w.strip()]
        if not words:
            return [], 0

        safe_query_parts = [f'"{w}"' for w in words]
        safe_query = " ".join(safe_query_parts)
        match_expr = safe_query

        # Modify match_expr based on scope
        if scope == "filename":
            match_expr = f'filename : {safe_query}'
        elif scope == "content":
            match_expr = f'text_content : {safe_query}'
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
            raw_snip = r["snippet"]

            # HTML Escape the snippet to prevent XSS, but preserve the FTS5 <mark> tags
            # We temporarily replace <mark> with a unique placeholder, escape the rest, and restore <mark>
            snip = None
            if raw_snip:
                safe_snip = raw_snip.replace('<mark>', '[[[MARK_START]]]').replace('</mark>', '[[[MARK_END]]]')
                safe_snip = html.escape(safe_snip)
                snip = safe_snip.replace('[[[MARK_START]]]', '<mark>').replace('[[[MARK_END]]]', '</mark>')

            # If the search was restricted to filename, source is filename
            if scope == "filename":
                match_source = "filename"
                snip = None
            elif not raw_snip or raw_snip == "..." or "<mark>" not in raw_snip:
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

    def get_suggestions(self, query: str, limit: int = 8) -> list[dict]:
        query = query.strip()
        if len(query) < 2:
            return []

        conn = get_connection()

        # 优先前缀匹配
        prefix_sql = """
            SELECT id, filename, current_path
            FROM file_records
            WHERE status = 'active' AND filename LIKE ?
            LIMIT ?
        """
        prefix_rows = conn.execute(prefix_sql, (f"{query}%", limit)).fetchall()

        results = []
        seen_files = set()

        for r in prefix_rows:
            results.append({
                "type": "filename",
                "text": r["filename"],
                "file_id": r["id"],
                "path": r["current_path"]
            })
            seen_files.add(r["id"])

        # 如果不够，补充包含匹配
        remaining = limit - len(results)
        if remaining > 0:
            contains_sql = """
                SELECT id, filename, current_path
                FROM file_records
                WHERE status = 'active' AND filename LIKE ?
                LIMIT ?
            """
            contains_rows = conn.execute(contains_sql, (f"%{query}%", remaining + len(results))).fetchall()

            for r in contains_rows:
                if r["id"] not in seen_files:
                    results.append({
                        "type": "filename",
                        "text": r["filename"],
                        "file_id": r["id"],
                        "path": r["current_path"]
                    })
                    seen_files.add(r["id"])
                    if len(results) >= limit:
                        break

        return results
