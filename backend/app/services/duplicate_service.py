from ..models.file_suggestion import FileSuggestion
from ..models.scan_task import now_iso
from ..repositories.file_repository import FileRepository
from ..repositories.suggestion_repository import SuggestionRepository


class DuplicateService:
    def __init__(self) -> None:
        self.file_repo = FileRepository()
        self.sug_repo = SuggestionRepository()

    def find_groups(self) -> list[dict]:
        return self.file_repo.find_duplicate_groups()

    def create_duplicate_suggestions(self, sha256: str, keep_file_id: int) -> int:
        """Move all files in a duplicate group (except the kept one) to Duplicates/."""
        groups = self.file_repo.find_duplicate_groups()
        group = next((g for g in groups if g["sha256"] == sha256), None)
        if not group:
            return 0

        created = 0
        for f in group["files"]:
            if f["id"] == keep_file_id:
                continue
            file_rec = self.file_repo.get(f["id"])
            if not file_rec:
                continue

            from pathlib import Path
            src = Path(file_rec.current_path)
            target = src.parent / "Duplicates" / src.name

            suggestion = FileSuggestion(
                file_id=file_rec.id,
                suggestion_type="move_duplicate",
                source_path=file_rec.current_path,
                target_path=str(target),
                reason="Duplicate file, suggested to move to Duplicates directory",
                confidence=0.9,
                conflict_status="none",
                status="pending",
                created_at=now_iso(),
            )
            self.sug_repo.create(suggestion)
            created += 1

        return created
