from fastapi import Depends
from functools import lru_cache

from .services.path_protection_service import PathProtectionService
from .services.llm_provider_service import LLMProviderService
from .services.ai_classification_service import AIClassificationService
from .services.organize_plan_service import OrganizePlanService
from .services.ai_rule_draft_service import AIRuleDraftService
from .services.ai_task_queue_service import AITaskQueueService
from .repositories.settings_repository import SettingsRepository
from .repositories.file_repository import FileRepository
from .repositories.suggestion_repository import SuggestionRepository

def get_path_protection_service() -> PathProtectionService:
    return PathProtectionService()

def get_llm_provider_service() -> LLMProviderService:
    return LLMProviderService()

def get_ai_classification_service(
    path_protection: PathProtectionService = Depends(get_path_protection_service),
    llm_service: LLMProviderService = Depends(get_llm_provider_service),
) -> AIClassificationService:
    return AIClassificationService(
        path_protection=path_protection,
        llm_service=llm_service,
    )

def get_organize_plan_service(
    path_protection: PathProtectionService = Depends(get_path_protection_service),
    classification_service: AIClassificationService = Depends(get_ai_classification_service),
) -> OrganizePlanService:
    return OrganizePlanService(
        path_protection=path_protection,
        classification_service=classification_service,
    )

def get_ai_rule_draft_service(
    path_protection: PathProtectionService = Depends(get_path_protection_service),
    llm_service: LLMProviderService = Depends(get_llm_provider_service),
) -> AIRuleDraftService:
    return AIRuleDraftService(
        path_protection=path_protection,
        llm_service=llm_service,
    )

@lru_cache()
def get_ai_task_queue_service() -> AITaskQueueService:
    return AITaskQueueService()

def get_settings_repository() -> SettingsRepository:
    return SettingsRepository()

def get_file_repository() -> FileRepository:
    return FileRepository()

def get_suggestion_repository() -> SuggestionRepository:
    return SuggestionRepository()
