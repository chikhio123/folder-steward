import json
from typing import List, Dict, Any
from pathlib import Path
from ..core.database import get_connection
from ..models.scan_task import now_iso
from ..models.organize_plan import OrganizePlan
from ..models.organize_plan_item import OrganizePlanItem
from ..models.file_suggestion import FileSuggestion
from ..repositories.organize_plan_repository import OrganizePlanRepository
from ..repositories.ai_classification_repository import AIClassificationRepository
from ..repositories.suggestion_repository import SuggestionRepository

class OrganizePlanService:
    def __init__(self):
        self.plan_repo = OrganizePlanRepository()
        self.ai_sug_repo = AIClassificationRepository()
        self.sug_repo = SuggestionRepository()

    def generate_plan(self, scope: str, min_confidence: float = 0.65) -> int:
        """Aggregates recent pending AI classification suggestions into a structured plan."""
        conn = get_connection()
        row = conn.execute("SELECT value FROM app_settings WHERE key = 'archive_root'").fetchone()
        archive_root = row["value"] if row else ""

        # Fetch pending AI suggestions that meet confidence
        rows = conn.execute(
            """SELECT a.*, f.current_path
               FROM ai_classification_suggestions a
               JOIN file_records f ON a.file_id = f.id
               WHERE a.status = 'pending' AND a.confidence >= ?
            """, (min_confidence,)
        ).fetchall()

        if not rows:
            raise ValueError("No pending AI classification suggestions found with sufficient confidence.")

        plan = OrganizePlan(
            title=f"AI Organize Plan ({scope})",
            scope=scope,
            status="draft",
            created_at=now_iso()
        )
        plan_id = self.plan_repo.create_plan(plan)

        summary_counts = {}

        for r in rows:
            target_dir = r["suggested_target_dir"]
            # Increment summary
            summary_counts[target_dir] = summary_counts.get(target_dir, 0) + 1

            target_path = str(Path(archive_root) / target_dir / Path(r["current_path"]).name)

            item = OrganizePlanItem(
                plan_id=plan_id,
                file_id=r["file_id"],
                source_path=r["current_path"],
                target_dir=target_dir,
                target_path=target_path,
                directory_status=r["directory_status"],
                confidence=r["confidence"],
                reason=r["reason"],
                evidence_json=r["evidence_json"],
                status="pending",
                created_at=now_iso()
            )
            self.plan_repo.create_item(item)

            # Mark AI suggestion as in_plan so it doesn't get picked up again
            conn.execute("UPDATE ai_classification_suggestions SET status='in_plan' WHERE id=?", (r["id"],))

        plan.summary_json = json.dumps(summary_counts, ensure_ascii=False)
        self.plan_repo.update_plan(plan)
        conn.commit()

        return plan_id

    def get_plan_preview(self, plan_id: int) -> Dict[str, Any]:
        plan = self.plan_repo.get_plan(plan_id)
        if not plan:
            return {}

        items = self.plan_repo.get_items_by_plan(plan_id)

        grouped = {}
        for item in items:
            if item.target_dir not in grouped:
                grouped[item.target_dir] = []
            grouped[item.target_dir].append({
                "item_id": item.id,
                "file_id": item.file_id,
                "source_path": item.source_path,
                "target_path": item.target_path,
                "directory_status": item.directory_status,
                "confidence": item.confidence,
                "reason": item.reason
            })

        return {
            "plan_id": plan.id,
            "title": plan.title,
            "status": plan.status,
            "groups": grouped
        }

    def accept_plan(self, plan_id: int) -> None:
        """Converts accepted plan items into actual file_suggestions."""
        plan = self.plan_repo.get_plan(plan_id)
        if not plan or plan.status != "draft":
            raise ValueError("Plan not found or not in draft status.")

        items = self.plan_repo.get_items_by_plan(plan_id)
        accepted_items = [i for i in items if i.status == "pending"]

        if not accepted_items:
            raise ValueError("No pending items to accept.")

        conn = get_connection()
        row = conn.execute("SELECT value FROM app_settings WHERE key = 'archive_root'").fetchone()
        archive_root = row["value"] if row else ""

        for item in accepted_items:
            # Create real suggestion
            sug = FileSuggestion(
                file_id=item.file_id,
                suggestion_type="move",
                source_path=item.source_path,
                target_path=item.target_path,
                reason=item.reason,
                confidence=item.confidence,
                conflict_status="none", # simplified, real system would check target_exists
                status="pending",
                archive_root=archive_root,
                created_at=now_iso()
            )
            self.sug_repo.create(sug)

            # Mark item converted
            conn.execute("UPDATE organize_plan_items SET status='converted' WHERE id=?", (item.id,))
            # Mark original suggestion as converted
            conn.execute("UPDATE ai_classification_suggestions SET status='converted' WHERE file_id=? AND status='in_plan'", (item.file_id,))

        # Mark plan converted
        plan.status = "converted"
        plan.updated_at = now_iso()
        self.plan_repo.update_plan(plan)
        conn.commit()

    def reject_plan(self, plan_id: int) -> None:
        """Rejects a plan and restores its items' original classification suggestions to pending."""
        plan = self.plan_repo.get_plan(plan_id)
        if not plan or plan.status != "draft":
            raise ValueError("Plan not found or not in draft status.")

        conn = get_connection()
        items = self.plan_repo.get_items_by_plan(plan_id)

        for item in items:
            conn.execute("UPDATE organize_plan_items SET status='rejected' WHERE id=?", (item.id,))
            conn.execute("UPDATE ai_classification_suggestions SET status='pending' WHERE file_id=? AND status='in_plan'", (item.file_id,))

        plan.status = "rejected"
        plan.updated_at = now_iso()
        self.plan_repo.update_plan(plan)
        conn.commit()
