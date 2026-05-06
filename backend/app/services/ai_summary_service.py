import json
from typing import Optional
from ..models.file_summary import FileSummary
from ..models.scan_task import now_iso
from ..repositories.file_summary_repository import FileSummaryRepository
from .prompt_context_service import PromptContextService
from .llm_provider_service import LLMProviderService

class AISummaryService:
    def __init__(self):
        self.summary_repo = FileSummaryRepository()
        self.context_service = PromptContextService()
        self.llm_service = LLMProviderService()

    def process_summary_task(self, file_id: int) -> None:
        """Generates and saves a summary for a specific file."""
        # 1. Build Context
        file_context = self.context_service.build_file_context(file_id, max_preview_length=3000)
        if not file_context:
            return

        # 2. Call LLM
        try:
            summary_text = self.llm_service.generate_summary(file_context)

            # Check if exists, if so update it, else create
            existing = self.summary_repo.get_by_file_id(file_id)
            if existing:
                existing.summary = summary_text
                existing.status = "completed"
                existing.updated_at = now_iso()
                existing.llm_provider = self.llm_service.provider_type
                existing.model_name = "mock-model"
                self.summary_repo.update(existing)
            else:
                new_summary = FileSummary(
                    file_id=file_id,
                    summary=summary_text,
                    llm_provider=self.llm_service.provider_type,
                    model_name="mock-model",
                    status="completed",
                    created_at=now_iso()
                )
                self.summary_repo.create(new_summary)

        except Exception as e:
            existing = self.summary_repo.get_by_file_id(file_id)
            if existing:
                existing.status = "failed"
                existing.error_message = str(e)
                existing.updated_at = now_iso()
                self.summary_repo.update(existing)
            else:
                new_summary = FileSummary(
                    file_id=file_id,
                    summary="",
                    status="failed",
                    error_message=str(e),
                    created_at=now_iso()
                )
                self.summary_repo.create(new_summary)
