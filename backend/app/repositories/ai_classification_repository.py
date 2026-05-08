from typing import Optional
from ..core.database import get_connection
from ..models.ai_classification_suggestion import AIClassificationSuggestion

class AIClassificationRepository:
    def create(self, suggestion: AIClassificationSuggestion) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO ai_classification_suggestions
               (file_id, suggested_target_dir, directory_status, confidence,
                reason, evidence_json, source_context_hash, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (suggestion.file_id, suggestion.suggested_target_dir, suggestion.directory_status,
             suggestion.confidence, suggestion.reason, suggestion.evidence_json,
             suggestion.source_context_hash, suggestion.status,
             suggestion.created_at, suggestion.updated_at),
        )
        conn.commit()
        return cur.lastrowid

    def get(self, sug_id: int) -> Optional[AIClassificationSuggestion]:
        row = get_connection().execute(
            "SELECT * FROM ai_classification_suggestions WHERE id = ?", (sug_id,)
        ).fetchone()
        if not row:
            return None
        return AIClassificationSuggestion(**dict(row))

    def update(self, suggestion: AIClassificationSuggestion) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE ai_classification_suggestions SET
               suggested_target_dir=?, directory_status=?, confidence=?, reason=?,
               evidence_json=?, source_context_hash=?, status=?, updated_at=?
               WHERE id=?""",
            (suggestion.suggested_target_dir, suggestion.directory_status,
             suggestion.confidence, suggestion.reason, suggestion.evidence_json,
             suggestion.source_context_hash, suggestion.status,
             suggestion.updated_at, suggestion.id),
        )
        conn.commit()

    def delete_pending_by_files(self, file_ids: list[int]) -> None:
        if not file_ids:
            return
        conn = get_connection()
        chunk_size = 500
        for i in range(0, len(file_ids), chunk_size):
            chunk = file_ids[i:i+chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            conn.execute(f"DELETE FROM ai_classification_suggestions WHERE status = 'pending' AND file_id IN ({placeholders})", chunk)
        conn.commit()

    def update_status_batch(self, suggestion_ids: list[int], status: str) -> None:
        if not suggestion_ids:
            return
        conn = get_connection()
        chunk_size = 500
        for i in range(0, len(suggestion_ids), chunk_size):
            chunk = suggestion_ids[i:i+chunk_size]
            placeholders = ",".join("?" for _ in chunk)
            # Need to pass status first, then the chunk IDs
            params = [status] + chunk
            conn.execute(f"UPDATE ai_classification_suggestions SET status=? WHERE id IN ({placeholders})", params)
        conn.commit()

    def get_pending_with_paths(self, file_ids: list[int], min_confidence: float) -> list[dict]:
        if not file_ids:
            return []
        conn = get_connection()
        placeholders = ",".join("?" for _ in file_ids)
        rows = conn.execute(
            f"""SELECT a.id as suggestion_id, a.*, f.current_path
               FROM ai_classification_suggestions a
               JOIN file_records f ON a.file_id = f.id
               WHERE a.status = 'pending' AND a.confidence >= ?
                 AND a.file_id IN ({placeholders})
            """, (min_confidence, *file_ids)
        ).fetchall()
        return [dict(r) for r in rows]
