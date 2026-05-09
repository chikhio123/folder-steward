import json
from typing import List, Dict, Any
from pathlib import Path

from ..models.scan_task import now_iso
from ..models.organize_plan import OrganizePlan
from ..models.organize_plan_item import OrganizePlanItem
from ..models.file_suggestion import FileSuggestion
from ..repositories.organize_plan_repository import OrganizePlanRepository
from ..repositories.ai_classification_repository import AIClassificationRepository
from ..repositories.suggestion_repository import SuggestionRepository
from .path_protection_service import PathProtectionService

class OrganizePlanService:
    def __init__(
        self,
        plan_repo=None,
        class_repo=None,
        suggestion_repo=None,
        path_protection=None,
        classification_service=None,
        settings_repo=None,
        file_repo=None,
    ):
        self.plan_repo = plan_repo or OrganizePlanRepository()
        self.ai_sug_repo = class_repo or AIClassificationRepository()
        self.sug_repo = suggestion_repo or SuggestionRepository()
        self.path_protection = path_protection or PathProtectionService()
        self.classification_service = classification_service or None

        from ..repositories.settings_repository import SettingsRepository
        from ..repositories.file_repository import FileRepository
        self.settings_repo = settings_repo or SettingsRepository()
        self.file_repo = file_repo or FileRepository()


    def generate_plan(self, scope: str, min_confidence: float = 0.65, task=None) -> int:
        """Classifies files and aggregates suggestions into a structured plan."""
        from .ai_classification_service import AIClassificationService
        class_service = self.classification_service or AIClassificationService(
            path_protection=self.path_protection
        )

        archive_root = self.settings_repo.get("archive_root") or ""

        if not archive_root:
            raise ValueError("archive_root is not configured")

        # Find files to classify based on scope
        if scope == "others":
            # Files not matched by any rules yet (this is simplified)
            # We exclude files already inside the archive_root
            if archive_root:
                archive_prefix = str(Path(archive_root).resolve())
                file_ids = self.file_repo.get_active_excluding_prefix(archive_prefix)
            else:
                file_ids = self.file_repo.get_all_active_ids()
        else:
            file_ids = self.file_repo.get_all_active_ids()

        # 过滤排除目录（防线2：generate_plan 入口）
        path_protection = self.path_protection
        file_ids, skipped = path_protection.filter_file_ids(file_ids)
        if skipped > 0:
            print(f"Skipped {skipped} files due to AI exclude paths")

        if not file_ids:
            raise ValueError("应用 AI 排除目录后，没有可处理的文件。")

        # Reject any existing draft plans to avoid orphaned plans locking files
        conn = get_connection()
        draft_plans = conn.execute("SELECT id FROM organize_plans WHERE status = 'draft'").fetchall()
        for dp in draft_plans:
            try:
                self.reject_plan(dp["id"])
            except Exception as e:
                print(f"Failed to auto-reject orphaned plan {dp['id']}: {e}")

        if task:
            task.total_items = len(file_ids)
            from ..repositories.ai_task_repository import AITaskRepository
            task_repo = AITaskRepository()
            task_repo.update(task)

        # Clear existing pending suggestions for these files so we start fresh
        if file_ids:
            self.ai_sug_repo.delete_pending_by_files(file_ids)

        # Classify all target files in batches
        class_service.process_classification_batch(file_ids, archive_root, batch_size=20, task=task)

        # Check if task was cancelled
        if task:
            from ..repositories.ai_task_repository import AITaskRepository
            current_task = AITaskRepository().get(task.id)
            if current_task and current_task.status == "failed" and "Cancelled" in (current_task.error_message or ""):
                raise ValueError("Plan generation cancelled by user.")

        # Fetch pending AI suggestions that meet confidence, limited to current file_ids
        rows = self.ai_sug_repo.get_pending_with_paths(file_ids, min_confidence)

        if not rows:
            raise ValueError("No pending AI classification suggestions found with sufficient confidence.")
        plan = OrganizePlan(
            title=f"AI Organize Plan ({scope})",
            scope=scope,
            status="draft",
            created_at=now_iso()
        )
        plan_id = self.plan_repo.create_plan(plan)
        plan.id = plan_id

        summary_counts = {}

        for r in rows:
            target_dir = r["suggested_target_dir"]
            # Increment summary
            summary_counts[target_dir] = summary_counts.get(target_dir, 0) + 1

            target_path = str(Path(archive_root) / target_dir / Path(r["current_path"]).name)

            item = OrganizePlanItem(
                plan_id=plan_id,
                file_id=r["file_id"],
                ai_suggestion_id=r["suggestion_id"],
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
        suggestion_ids_to_update = [r["suggestion_id"] for r in rows]
        if suggestion_ids_to_update:
            self.ai_sug_repo.update_status_batch(suggestion_ids_to_update, "in_plan")

        plan.summary_json = json.dumps(summary_counts, ensure_ascii=False)
        self.plan_repo.update_plan(plan)

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

        archive_root = self.settings_repo.get("archive_root") or ""

        def create_sug_callback(conn, item):
            sug = FileSuggestion(
                file_id=item.file_id,
                suggestion_type="move",
                source_path=item.source_path,
                target_path=item.target_path,
                reason=item.reason,
                confidence=item.confidence,
                conflict_status="none",
                status="pending",
                archive_root=archive_root,
                created_at=now_iso()
            )
            self.sug_repo.create_with_conn(conn, sug)

        self.plan_repo.commit_accept_plan(plan, accepted_items, create_sug_callback)

    def reject_plan(self, plan_id: int) -> None:
        """Rejects a plan and restores its items' original classification suggestions to pending."""
        plan = self.plan_repo.get_plan(plan_id)
        if not plan or plan.status != "draft":
            raise ValueError("Plan not found or not in draft status.")

        items = self.plan_repo.get_items_by_plan(plan_id)
        self.plan_repo.commit_reject_plan(plan, items)
