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
