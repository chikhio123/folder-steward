from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from ..models.file_record import FileRecord
from ..models.file_content import FileContent
from ..models.rule import Rule
from ..repositories.rule_repository import RuleRepository

@dataclass
class RuleMatch:
    rule: Rule
    confidence: float
    reason: str

class RuleEngineService:
    def __init__(self) -> None:
        self.rule_repo = RuleRepository()

    def match(self, file_record: FileRecord, content: Optional[FileContent]) -> Optional[RuleMatch]:
        rules = self.rule_repo.list_all(only_enabled=True)
        if not rules:
            return None

        for rule in rules:
            if rule.rule_type == "extension":
                exts = [e.strip().lower() for e in rule.pattern.split(",")]
                if file_record.extension and file_record.extension.lower() in exts:
                    return RuleMatch(
                        rule=rule,
                        confidence=0.75,
                        reason=f"扩展名匹配规则 '{rule.name}' → {rule.target_dir}"
                    )

            elif rule.rule_type == "filename_keyword":
                keywords = [k.strip().lower() for k in rule.pattern.split(",")]
                fname = file_record.filename.lower()
                if any(kw in fname for kw in keywords if kw):
                    return RuleMatch(
                        rule=rule,
                        confidence=0.9,
                        reason=f"文件名关键词匹配规则 '{rule.name}' → {rule.target_dir}"
                    )

            elif rule.rule_type == "content_keyword":
                if content and content.text_content:
                    keywords = [k.strip().lower() for k in rule.pattern.split(",")]
                    text_lower = content.text_content.lower()
                    if any(kw in text_lower for kw in keywords if kw):
                        return RuleMatch(
                            rule=rule,
                            confidence=0.85,
                            reason=f"正文关键词匹配规则 '{rule.name}' → {rule.target_dir}"
                        )

            # size_range and modified_time_range can be added in V3+

        return None

    def build_target_path(self, file_record: FileRecord, match: Optional[RuleMatch], archive_root: Path) -> Path:
        if match and match.rule.target_dir:
            return archive_root / match.rule.target_dir / file_record.filename

        # Default fallback
        ext = file_record.extension.lstrip(".") if file_record.extension else "NoExtension"
        return archive_root / "Others" / ext / file_record.filename
