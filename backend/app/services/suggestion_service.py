from pathlib import Path
from typing import Optional

from ..core.database import get_connection
from ..models.file_record import FileRecord
from ..models.file_suggestion import FileSuggestion
from ..models.scan_task import now_iso
from ..repositories.file_repository import FileRepository
from ..repositories.suggestion_repository import SuggestionRepository


class ExtensionRule:
    def __init__(self, extensions: list[str], category: str) -> None:
        self.extensions = [e.lower() for e in extensions]
        self.category = category

    def match(self, file: FileRecord) -> Optional[str]:
        if file.extension and file.extension.lower() in self.extensions:
            return self.category
        return None


class KeywordRule:
    def __init__(self, keywords: list[str], category: str) -> None:
        self.keywords = [k.lower() for k in keywords]
        self.category = category

    def match(self, file: FileRecord) -> Optional[str]:
        name = file.filename.lower()
        if any(kw in name for kw in self.keywords):
            return self.category
        return None


EXTENSION_RULES = [
    ExtensionRule([".pdf"], "Documents/PDF"),
    ExtensionRule([".doc", ".docx"], "Documents/Word"),
    ExtensionRule([".xls", ".xlsx"], "Documents/Excel"),
    ExtensionRule([".ppt", ".pptx"], "Documents/PowerPoint"),
    ExtensionRule([".md", ".txt"], "Notes"),
    ExtensionRule([".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"], "Images"),
    ExtensionRule([".zip", ".rar", ".7z", ".tar", ".gz"], "Archives"),
    ExtensionRule([".mp4", ".mov", ".avi", ".mkv", ".webm"], "Videos"),
    ExtensionRule([".mp3", ".wav", ".flac", ".aac"], "Audio"),
    ExtensionRule([".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".rs", ".go"], "Code"),
]

KEYWORD_RULES = [
    KeywordRule(["论文", "毕业", "开题", "thesis", "dissertation"], "University/Thesis"),
    KeywordRule(["发票", "invoice", "receipt", "收据"], "Finance/Receipts"),
    KeywordRule(["简历", "resume", "cv"], "Personal/Resume"),
    KeywordRule(["康德", "kant", "cpr"], "Books/Philosophy"),
    KeywordRule(["报告", "report", "总结"], "Work/Reports"),
    KeywordRule(["照片", "photo", "screenshot", "截图"], "Images/Screenshots"),
]


class SuggestionService:
    def __init__(self) -> None:
        self.file_repo = FileRepository()
        self.sug_repo = SuggestionRepository()

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
            target = self._build_target(file_rec, archive)
            if target is None:
                skipped += 1
                continue

            target_str = str(target)
            conflict = self._check_conflict(target_str)

            self.sug_repo.mark_superseded_for_file(file_rec.id)

            suggestion = FileSuggestion(
                file_id=file_rec.id,
                suggestion_type="move",
                source_path=file_rec.current_path,
                target_path=target_str,
                reason=self._get_reason(file_rec),
                confidence=self._calc_confidence(file_rec),
                conflict_status=conflict,
                status="pending",
                archive_root=str(archive),
                created_at=now_iso(),
            )
            self.sug_repo.create(suggestion)
            created += 1

        return created, skipped

    def _build_target(self, file: FileRecord, archive_root: Path) -> Optional[Path]:
        # Keyword rules first (highest priority)
        for rule in KEYWORD_RULES:
            cat = rule.match(file)
            if cat:
                return archive_root / cat / file.filename

        # Extension rules second
        for rule in EXTENSION_RULES:
            cat = rule.match(file)
            if cat:
                return archive_root / cat / file.filename

        # Default: Others/{extension}
        ext = file.extension.lstrip(".") if file.extension else "NoExtension"
        return archive_root / "Others" / ext / file.filename

    def _check_conflict(self, target_path: str) -> str:
        if Path(target_path).exists():
            return "target_exists"
        return "none"

    def _get_reason(self, file: FileRecord) -> str:
        for rule in KEYWORD_RULES:
            cat = rule.match(file)
            if cat:
                return f"文件名匹配关键词规则 → {cat}"
        for rule in EXTENSION_RULES:
            cat = rule.match(file)
            if cat:
                return f"{file.extension} 文件 → {cat}"
        ext = file.extension.lstrip(".") if file.extension else "NoExtension"
        return f"未分类文件 → Others/{ext}"

    def _calc_confidence(self, file: FileRecord) -> float:
        for rule in KEYWORD_RULES:
            if rule.match(file):
                return 0.9
        for rule in EXTENSION_RULES:
            if rule.match(file):
                return 0.75
        return 0.5
