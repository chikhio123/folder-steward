from pathlib import Path
from typing import Optional

from ..core.database import get_connection
from ..models.file_record import FileRecord
from ..models.file_suggestion import FileSuggestion
from ..models.scan_task import now_iso
from ..repositories.file_repository import FileRepository
from ..repositories.suggestion_repository import SuggestionRepository
from ..repositories.file_content_repository import FileContentRepository
from .rule_engine_service import RuleEngineService

class SuggestionService:
    def __init__(self) -> None:
        self.file_repo = FileRepository()
        self.sug_repo = SuggestionRepository()
        self.content_repo = FileContentRepository()
        self.rule_engine = RuleEngineService()

    def generate_suggestions(self, archive_root: str) -> tuple[int, int]:
        archive = Path(archive_root).resolve()
        # Store archive_root for later validation (PATCH, execute)
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            ("archive_root", str(archive), now_iso()),
        )
        conn.commit()
        all_files, _ = self.file_repo.list_paginated(page=1, page_size=99999)

        created = 0
        skipped = 0

        for file_rec in all_files:
            content = self.content_repo.get_by_file_id(file_rec.id)
            match = self.rule_engine.match(file_rec, content)

            target = self.rule_engine.build_target_path(file_rec, match, archive)
            if target is None:
                skipped += 1
                continue

            target_str = str(target)
            conflict = self._check_conflict(target_str)

            self.sug_repo.mark_superseded_for_file(file_rec.id)

            reason = match.reason if match else f"未匹配自定义规则，使用默认分类 → Others/{file_rec.extension.lstrip('.') if file_rec.extension else 'NoExtension'}"
            confidence = match.confidence if match else 0.5

            suggestion = FileSuggestion(
                file_id=file_rec.id,
                suggestion_type="move",
                source_path=file_rec.current_path,
                target_path=target_str,
                reason=reason,
                confidence=confidence,
                conflict_status=conflict,
                status="pending",
                archive_root=str(archive),
                created_at=now_iso(),
            )
            self.sug_repo.create(suggestion)
            created += 1

        return created, skipped

    def _check_conflict(self, target_path: str) -> str:
        if Path(target_path).exists():
            return "target_exists"
        return "none"
