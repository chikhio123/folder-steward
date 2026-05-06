from typing import List
from ..core.database import get_connection
from ..models.scan_task import now_iso
from ..models.ai_classification_suggestion import AIClassificationSuggestion
from ..repositories.ai_classification_repository import AIClassificationRepository
from .prompt_context_service import PromptContextService
from .llm_provider_service import LLMProviderService
from .directory_policy_service import DirectoryPolicyService

class AIClassificationService:
    def __init__(self):
        self.class_repo = AIClassificationRepository()
        self.context_service = PromptContextService()
        self.llm_service = LLMProviderService()
        self.dir_policy = DirectoryPolicyService()

    def process_classification_task(self, file_id: int, archive_root: str) -> None:
        """Processes an AI classification task for a single file and saves the result."""
        # 1. Build context
        file_context = self.context_service.build_file_context(file_id, max_preview_length=800)
        rules_context = self.context_service.build_rules_context()

        if not file_context:
            return

        # 2. Call LLM
        result = self.llm_service.generate_classification(file_context, rules_context, archive_root)

        target_dir = result.get("suggested_target_dir", "")
        # 3. Policy Check
        policy_status = self.dir_policy.evaluate(target_dir, archive_root)
        status = "pending"
        if policy_status == "invalid":
            status = "failed"

        # Note: we need the content hash for stale detection. For M6/M7, we'll just mock it or grab it if needed.
        # Actually, the trigger on `file_contents` sets it to stale automatically, we don't strictly need a hash here
        # since SQLite triggers handle it directly via file_id.

        sug = AIClassificationSuggestion(
            file_id=file_id,
            suggested_target_dir=target_dir,
            directory_status=policy_status,
            confidence=result.get("confidence", 0.0),
            reason=result.get("reason"),
            evidence_json=None, # Mocked list could be JSON encoded here
            source_context_hash=None,
            status=status,
            created_at=now_iso()
        )
        self.class_repo.create(sug)
