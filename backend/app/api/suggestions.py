from fastapi import APIRouter, HTTPException, Query, Depends
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from ..schemas.suggestion_schema import (
    GenerateSuggestionsRequest,
    GenerateSuggestionsResponse,
    FileSuggestionResponse,
    SuggestionListResponse,
    UpdateSuggestionRequest,
    SuggestionStatus,
)
from ..repositories.suggestion_repository import SuggestionRepository
from ..repositories.settings_repository import SettingsRepository
from ..dependencies import get_settings_repository, get_suggestion_repository

router = APIRouter(tags=["suggestions"])

@router.post("/suggestions/generate", response_model=GenerateSuggestionsResponse)
def generate_suggestions(
    body: GenerateSuggestionsRequest,
    settings_repo: SettingsRepository = Depends(get_settings_repository)
):
    from ..services.suggestion_service import SuggestionService
    svc = SuggestionService()
    archive_root = _get_archive_root(settings_repo, body.archive_root)
    created, skipped = svc.generate_suggestions(archive_root)
    return GenerateSuggestionsResponse(created_count=created, skipped_count=skipped)


@router.get("/suggestions", response_model=SuggestionListResponse)
def list_suggestions(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    suggestion_repo: SuggestionRepository = Depends(get_suggestion_repository)
):
    items, total = suggestion_repo.list_paginated(status=status, page=page, page_size=page_size)
    return SuggestionListResponse(
        items=[
            FileSuggestionResponse(
                id=s.id,
                file_id=s.file_id,
                suggestion_type=s.suggestion_type,
                source_path=s.source_path,
                target_path=s.target_path,
                reason=s.reason,
                confidence=s.confidence,
                conflict_status=s.conflict_status,
                status=s.status,
            )
            for s in items
        ],
        total=total,
    )


def _get_archive_root(settings_repo: SettingsRepository, suggestion_archive_root: Optional[str] = None) -> str:
    if suggestion_archive_root:
        return suggestion_archive_root
    return settings_repo.get("archive_root") or ""


class BulkRejectRequest(BaseModel):
    status: SuggestionStatus = "pending"

from ..core.uow import UnitOfWork

@router.post("/suggestions/bulk-reject")
def bulk_reject_suggestions(
    body: BulkRejectRequest,
    suggestion_repo: SuggestionRepository = Depends(get_suggestion_repository)
):
    """Reject all suggestions matching the optional status filter."""
    with UnitOfWork():
        rejected_count = suggestion_repo.bulk_update_status(body.status.value, "rejected")
    return {"status": "success", "rejected_count": rejected_count}


@router.patch("/suggestions/{suggestion_id}", response_model=FileSuggestionResponse)
def update_suggestion(
    suggestion_id: int, 
    body: UpdateSuggestionRequest,
    suggestion_repo: SuggestionRepository = Depends(get_suggestion_repository),
    settings_repo: SettingsRepository = Depends(get_settings_repository)
):
    suggestion = suggestion_repo.get(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if body.target_path is not None:
        archive_root = _get_archive_root(settings_repo, suggestion.archive_root)
        if archive_root:
            target = Path(body.target_path).resolve()
            root = Path(archive_root).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Target path must be within archive root: {archive_root}",
                )
        suggestion.target_path = body.target_path
    if body.status is not None:
        suggestion.status = body.status
        
    with UnitOfWork():
        suggestion_repo.update(suggestion)
        
    return FileSuggestionResponse(
        id=suggestion.id,
        file_id=suggestion.file_id,
        suggestion_type=suggestion.suggestion_type,
        source_path=suggestion.source_path,
        target_path=suggestion.target_path,
        reason=suggestion.reason,
        confidence=suggestion.confidence,
        conflict_status=suggestion.conflict_status,
        status=suggestion.status,
    )
