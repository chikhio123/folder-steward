from pathlib import Path
from ..models.file_suggestion import FileSuggestion
from ..models.scan_task import now_iso
from ..repositories.file_repository import FileRepository
from ..repositories.suggestion_repository import SuggestionRepository
from ..core.database import get_connection

class DuplicateService:
    def __init__(self) -> None:
        self.file_repo = FileRepository()
        self.sug_repo = SuggestionRepository()

    def find_groups(self) -> list[dict]:
        return self.file_repo.find_duplicate_groups()

    def get_archive_root(self) -> str:
        row = get_connection().execute("SELECT value FROM app_settings WHERE key = 'archive_root'").fetchone()
        return row["value"] if row else ""

    def get_unique_target_path(self, target: Path) -> Path:
        if not target.exists():
            return target

        base = target.stem
        ext = target.suffix
        parent = target.parent
        counter = 1

        while True:
            new_target = parent / f"{base}_{counter}{ext}"
            if not new_target.exists():
                return new_target
            counter += 1

    def is_file_in_active_plan(self, file_id: int) -> bool:
        conn = get_connection()
        row = conn.execute("""
            SELECT 1 FROM organize_plan_items opi
            JOIN organize_plans op ON opi.plan_id = op.id
            WHERE opi.file_id = ? AND op.status = 'draft' AND opi.status = 'pending'
        """, (file_id,)).fetchone()
        if row: return True

        row2 = conn.execute("""
            SELECT 1 FROM file_suggestions
            WHERE file_id = ? AND status IN ('pending', 'accepted')
        """, (file_id,)).fetchone()
        return bool(row2)

    def isolate_duplicates(self, groups: list[dict], auto_mode: bool = False) -> dict:
        """
        For each group, pick a keep_file_id (if auto_mode, pick best),
        move others to archive_root/Trash_Duplicates.
        Returns execution results using OperationService.
        """
        archive_root_str = self.get_archive_root()
        if not archive_root_str:
            raise ValueError("archive_root is not configured in settings")

        archive_root = Path(archive_root_str).resolve()
        trash_dir = archive_root / "Trash_Duplicates"

        suggestion_ids_to_execute = []
        skipped = []

        all_db_groups = self.file_repo.find_duplicate_groups()

        for input_group in groups:
            sha256 = input_group["sha256"]
            keep_file_id = input_group.get("keep_file_id")

            db_group = next((g for g in all_db_groups if g["sha256"] == sha256), None)
            if not db_group:
                continue

            files = db_group["files"]
            if len(files) < 2:
                continue

            if auto_mode or not keep_file_id:
                def score_file(f):
                    path = Path(f["current_path"]).resolve()
                    in_archive = 0 if path.is_relative_to(archive_root) else 1
                    depth = len(path.parts)
                    return (in_archive, depth, f["id"])

                sorted_files = sorted(files, key=score_file)
                keep_file_id = sorted_files[0]["id"]

            for f in files:
                if f["id"] == keep_file_id:
                    continue

                if self.is_file_in_active_plan(f["id"]):
                    skipped.append({"file_id": f["id"], "reason": "File is referenced by active organize plan or suggestion"})
                    continue

                file_rec = self.file_repo.get(f["id"])
                if not file_rec:
                    continue

                target = self.get_unique_target_path(trash_dir / file_rec.filename)

                suggestion = FileSuggestion(
                    file_id=file_rec.id,
                    suggestion_type="move_duplicate",
                    source_path=file_rec.current_path,
                    target_path=str(target),
                    reason="Duplicate file isolated",
                    confidence=1.0,
                    conflict_status="none",
                    status="accepted", # automatically accept
                    archive_root=archive_root_str,
                    created_at=now_iso(),
                )
                sug_id = self.sug_repo.create(suggestion)
                suggestion_ids_to_execute.append(sug_id)

        if not suggestion_ids_to_execute:
            return {"success_count": 0, "failed_count": 0, "results": [], "skipped": skipped}

        from .operation_service import OperationService
        op_service = OperationService()
        result = op_service.execute_suggestions(suggestion_ids_to_execute)
        result["skipped"] = skipped
        return result
