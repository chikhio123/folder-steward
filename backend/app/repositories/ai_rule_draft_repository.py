from typing import Optional
from ..core.database import get_connection
from ..models.ai_rule_draft import AIRuleDraft

class AIRuleDraftRepository:
    def create(self, draft: AIRuleDraft) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO ai_rule_drafts
               (user_prompt, name, rule_type, pattern, target_dir, action,
                priority, reason, confidence, status, validation_error, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (draft.user_prompt, draft.name, draft.rule_type, draft.pattern,
             draft.target_dir, draft.action, draft.priority, draft.reason,
             draft.confidence, draft.status, draft.validation_error,
             draft.created_at, draft.updated_at),
        )
        conn.commit()
        return cur.lastrowid

    def get(self, draft_id: int) -> Optional[AIRuleDraft]:
        row = get_connection().execute(
            "SELECT * FROM ai_rule_drafts WHERE id = ?", (draft_id,)
        ).fetchone()
        if not row:
            return None
        return AIRuleDraft(**dict(row))

    def update(self, draft: AIRuleDraft) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE ai_rule_drafts SET
               name=?, rule_type=?, pattern=?, target_dir=?, action=?,
               priority=?, reason=?, confidence=?, status=?, validation_error=?, updated_at=?
               WHERE id=?""",
            (draft.name, draft.rule_type, draft.pattern, draft.target_dir, draft.action,
             draft.priority, draft.reason, draft.confidence, draft.status, draft.validation_error,
             draft.updated_at, draft.id),
        )
        conn.commit()
