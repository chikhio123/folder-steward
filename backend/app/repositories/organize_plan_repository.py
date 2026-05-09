from typing import Optional
from ..core.database import get_connection
from ..models.organize_plan import OrganizePlan
from ..models.organize_plan_item import OrganizePlanItem

class OrganizePlanRepository:
    def create_plan(self, plan: OrganizePlan) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO organize_plans
               (title, scope, status, summary_json, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (plan.title, plan.scope, plan.status, plan.summary_json,
             plan.created_at, plan.updated_at),
        )
        conn.commit()
        return cur.lastrowid

    def get_plan(self, plan_id: int) -> Optional[OrganizePlan]:
        row = get_connection().execute(
            "SELECT * FROM organize_plans WHERE id = ?", (plan_id,)
        ).fetchone()
        if not row:
            return None
        return OrganizePlan(**dict(row))

    def update_plan(self, plan: OrganizePlan) -> None:
        conn = get_connection()
        conn.execute(
            """UPDATE organize_plans SET
               title=?, scope=?, status=?, summary_json=?, updated_at=?
               WHERE id=?""",
            (plan.title, plan.scope, plan.status, plan.summary_json,
             plan.updated_at, plan.id),
        )
        conn.commit()

    def create_item(self, item: OrganizePlanItem) -> int:
        conn = get_connection()
        cur = conn.execute(
            """INSERT INTO organize_plan_items
               (plan_id, file_id, ai_suggestion_id, source_path, target_dir, target_path, directory_status,
                confidence, reason, evidence_json, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (item.plan_id, item.file_id, item.ai_suggestion_id, item.source_path, item.target_dir,
             item.target_path, item.directory_status, item.confidence, item.reason,
             item.evidence_json, item.status, item.created_at, item.updated_at),
        )
        conn.commit()
        return cur.lastrowid

    def get_items_by_plan(self, plan_id: int) -> list[OrganizePlanItem]:
        rows = get_connection().execute(
            "SELECT * FROM organize_plan_items WHERE plan_id = ?", (plan_id,)
        ).fetchall()
        return [OrganizePlanItem(**dict(r)) for r in rows]

    def commit_accept_plan(self, plan: OrganizePlan, accepted_items: list[OrganizePlanItem], sug_repo_create_callback) -> None:
        conn = get_connection()
        conn.execute("BEGIN")
        try:
            for item in accepted_items:
                sug_repo_create_callback(item)
                conn.execute("UPDATE organize_plan_items SET status='converted' WHERE id=?", (item.id,))
                if item.ai_suggestion_id:
                    conn.execute("UPDATE ai_classification_suggestions SET status='converted' WHERE id=?", (item.ai_suggestion_id,))
            
            conn.execute(
                "UPDATE organize_plans SET title=?, scope=?, status=?, summary_json=?, updated_at=? WHERE id=?",
                (plan.title, plan.scope, "converted", plan.summary_json, plan.updated_at, plan.id)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def commit_reject_plan(self, plan: OrganizePlan, items: list[OrganizePlanItem]) -> None:
        conn = get_connection()
        conn.execute("BEGIN")
        try:
            for item in items:
                conn.execute("UPDATE organize_plan_items SET status='rejected' WHERE id=?", (item.id,))
                if item.ai_suggestion_id:
                    conn.execute("UPDATE ai_classification_suggestions SET status='pending' WHERE id=?", (item.ai_suggestion_id,))
            
            conn.execute(
                "UPDATE organize_plans SET title=?, scope=?, status=?, summary_json=?, updated_at=? WHERE id=?",
                (plan.title, plan.scope, "rejected", plan.summary_json, plan.updated_at, plan.id)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
