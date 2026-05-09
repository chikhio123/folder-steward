from pydantic import BaseModel
from typing import Optional, Literal

SuggestionStatus = Literal["pending", "accepted", "rejected", "executed", "failed", "superseded"]


class GenerateSuggestionsRequest(BaseModel):
    archive_root: Optional[str] = None


class GenerateSuggestionsResponse(BaseModel):
    created_count: int
    skipped_count: int


class FileSuggestionResponse(BaseModel):
    id: int
    file_id: int
    suggestion_type: str
    source_path: str
    target_path: str
    reason: Optional[str] = None
    confidence: float = 0
    conflict_status: str = "none"
    status: SuggestionStatus = "pending"


class SuggestionListResponse(BaseModel):
    items: list[FileSuggestionResponse]
    total: int


class UpdateSuggestionRequest(BaseModel):
    status: Optional[SuggestionStatus] = None
    target_path: Optional[str] = None
