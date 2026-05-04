from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..schemas.suggestion_schema import (
    GenerateSuggestionsRequest,
    GenerateSuggestionsResponse,
    FileSuggestionResponse,
    SuggestionListResponse,
    UpdateSuggestionRequest,
)
from ..repositories.suggestion_repository import SuggestionRepository

router = APIRouter(tags=["suggestions"])
suggestion_repo = SuggestionRepository()


@router.post("/suggestions/generate", response_model=GenerateSuggestionsResponse)
def generate_suggestions(body: GenerateSuggestionsRequest):
    from ..services.suggestion_service import SuggestionService
    svc = SuggestionService()
    created, skipped = svc.generate_suggestions(body.archive_root)
    return GenerateSuggestionsResponse(created_count=created, skipped_count=skipped)


@router.get("/suggestions", response_model=SuggestionListResponse)
def list_suggestions(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
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


@router.patch("/suggestions/{suggestion_id}", response_model=FileSuggestionResponse)
def update_suggestion(suggestion_id: int, body: UpdateSuggestionRequest):
    suggestion = suggestion_repo.get(suggestion_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    if body.status is not None:
        suggestion.status = body.status
    if body.target_path is not None:
        suggestion.target_path = body.target_path
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
