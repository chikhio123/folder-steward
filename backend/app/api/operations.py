from fastapi import APIRouter, HTTPException, Query

from ..schemas.operation_schema import (
    ExecuteSuggestionsRequest,
    ExecuteSuggestionsResponse,
    OperationResultItem,
    OperationLogResponse,
    OperationListResponse,
    RollbackResponse,
)
from ..repositories.operation_log_repository import OperationLogRepository

router = APIRouter(tags=["operations"])
op_repo = OperationLogRepository()


@router.post("/operations/execute-suggestions", response_model=ExecuteSuggestionsResponse)
def execute_suggestions(body: ExecuteSuggestionsRequest):
    from ..services.operation_service import OperationService
    svc = OperationService()
    result = svc.execute_suggestions(body.suggestion_ids)
    return ExecuteSuggestionsResponse(
        success_count=result["success_count"],
        failed_count=result["failed_count"],
        results=[
            OperationResultItem(**r) for r in result["results"]
        ],
    )


@router.get("/operations", response_model=OperationListResponse)
def list_operations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    items, total = op_repo.list_paginated(page=page, page_size=page_size)
    return OperationListResponse(
        items=[
            OperationLogResponse(
                id=o.id,
                operation_type=o.operation_type,
                source_path=o.source_path,
                target_path=o.target_path,
                status=o.status,
                rollback_available=bool(o.rollback_available),
                executed_at=o.executed_at,
                error_message=o.error_message,
            )
            for o in items
        ],
        total=total,
    )


@router.post("/operations/{operation_id}/rollback", response_model=RollbackResponse)
def rollback_operation(operation_id: int):
    from ..services.operation_service import OperationService
    svc = OperationService()
    try:
        result = svc.rollback_operation(operation_id)
        return RollbackResponse(operation_id=result["operation_id"], status=result["status"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
