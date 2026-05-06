from typing import Optional, List
from ..repositories.file_repository import FileRepository
from ..repositories.file_content_repository import FileContentRepository
from ..repositories.rule_repository import RuleRepository

class PromptContextService:
    def __init__(self):
        self.file_repo = FileRepository()
        self.content_repo = FileContentRepository()
        self.rule_repo = RuleRepository()

    def build_file_context(self, file_id: int, max_preview_length: int = 3000) -> Optional[dict]:
        """Build context for a single file including metadata and content preview."""
        file_rec = self.file_repo.get(file_id)
        if not file_rec:
            return None

        context = {
            "filename": file_rec.filename,
            "extension": file_rec.extension,
            "current_path": file_rec.current_path,
            "size_bytes": file_rec.size_bytes,
            "modified_at": file_rec.modified_at,
            "content_preview": None
        }

        content_rec = self.content_repo.get_by_file_id(file_id)
        if content_rec and content_rec.extract_status == "completed" and content_rec.text_content:
            text = content_rec.text_content
            if len(text) > max_preview_length:
                text = text[:max_preview_length] + "...[TRUNCATED]"
            context["content_preview"] = text

        return context

    def build_rules_context(self) -> List[dict]:
        """Return all active rules for the LLM to reference."""
        rules = self.rule_repo.list_all(only_enabled=True)
        return [
            {
                "name": r.name,
                "rule_type": r.rule_type,
                "pattern": r.pattern,
                "target_dir": r.target_dir,
                "priority": r.priority
            }
            for r in rules
        ]
