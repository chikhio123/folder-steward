import re

with open("D:/Code/Folder Steward/backend/app/services/ai_rule_draft_service.py", "r", encoding="utf-8") as f:
    content = f.read()

replacement = """    def get_preview(self, draft_id: int) -> dict:
        draft = self.draft_repo.get(draft_id)
        if not draft or draft.status != "validated":
            return {"draft_id": draft_id, "matched_count": 0, "items": []}

        archive_root = self._get_archive_root()
        archive_prefix = archive_root.rstrip("\\/") + "/" if archive_root else ""

        conn = get_connection()
        items = []
        
        if draft.rule_type == "extension":
            exts = [e.strip().lower() for e in draft.pattern.split(",") if e.strip()]
            placeholders = ",".join("?" for _ in exts)
            query = f"SELECT id, filename, current_path FROM file_records WHERE status='active' AND LOWER(extension) IN ({placeholders}) LIMIT 10"
            rows = conn.execute(query, exts).fetchall()
        elif draft.rule_type == "filename_keyword":
            keywords = [k.strip().lower() for k in draft.pattern.split(",") if k.strip()]
            where_clauses = " OR ".join(["LOWER(filename) LIKE ?"] * len(keywords))
            params = [f"%{k}%" for k in keywords]
            query = f"SELECT id, filename, current_path FROM file_records WHERE status='active' AND ({where_clauses}) LIMIT 10"
            if not keywords:
                rows = []
            else:
                rows = conn.execute(query, params).fetchall()
        elif draft.rule_type == "content_keyword":
            keywords = [k.strip().lower() for k in draft.pattern.split(",") if k.strip()]
            # FTS5 match query
            # OR logic for keywords
            match_query = " OR ".join(f'"{k}"' for k in keywords)
            query = "SELECT f.id, f.filename, f.current_path FROM file_content_fts fts JOIN file_records f ON fts.file_id = f.id WHERE f.status='active' AND file_content_fts MATCH ? LIMIT 10"
            if not keywords:
                rows = []
            else:
                rows = conn.execute(query, (match_query,)).fetchall()
        else:
            rows = []

        for r in rows:
            items.append({
                "file_id": r["id"],
                "filename": r["filename"],
                "current_path": r["current_path"],
                "target_path": f"{archive_prefix}{draft.target_dir}/{r['filename']}",
                "reason": draft.reason
            })

        return {
            "draft_id": draft_id,
            "matched_count": len(items), # Just an approximation for preview
            "items": items
        }"""

content = re.sub(r'    def get_preview\(self, draft_id: int\) -> dict:.*?(?=    def accept_draft)', replacement + "\n\n", content, flags=re.DOTALL)

with open("D:/Code/Folder Steward/backend/app/services/ai_rule_draft_service.py", "w", encoding="utf-8") as f:
    f.write(content)
