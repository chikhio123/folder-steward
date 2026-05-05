from fastapi import APIRouter, Query
from typing import Optional

from ..schemas.extract_task_schema import (
    CreateExtractTasksRequest,
    CreateExtractTasksResponse,
    ExtractTaskListResponse,
    ExtractTaskResponse,
)
from ..services.extract_service import ExtractService
from ..repositories.extract_task_repository import ExtractTaskRepository

router = APIRouter(tags=["extract-tasks"])
extract_service = ExtractService()
task_repo = ExtractTaskRepository()

@router.post("/extract-tasks", response_model=CreateExtractTasksResponse)
def create_extract_tasks(body: CreateExtractTasksRequest):
    created, skipped = extract_service.create_extract_tasks(body.file_ids, body.mode)
    return CreateExtractTasksResponse(created_count=created, skipped_count=skipped)

@router.get("/extract-tasks", response_model=ExtractTaskListResponse)
def list_extract_tasks(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    items, total = task_repo.list_paginated(status=status, page=page, page_size=page_size)
    return ExtractTaskListResponse(
        items=[
            ExtractTaskResponse(
                id=t.id,
                file_id=t.file_id,
                status=t.status,
                error_message=t.error_message,
                started_at=t.started_at,
                finished_at=t.finished_at,
            )
            for t in items
        ],
        total=total,
    )
