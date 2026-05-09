from pydantic import BaseModel
from typing import Optional


class ExecuteSuggestionsRequest(BaseModel):
    suggestion_ids: list[int]


class OperationResultItem(BaseModel):
    suggestion_id: int
    status: str
    operation_id: Optional[int] = None
    error_message: Optional[str] = None


class ExecuteSuggestionsResponse(BaseModel):
    success_count: int
    failed_count: int
    results: list[OperationResultItem]


class OperationLogResponse(BaseModel):
    id: int
    operation_type: str
    file_id: Optional[int] = None
    source_path: str
    target_path: Optional[str] = None
    status: str
    rollback_available: bool
    executed_at: str
    rollback_at: Optional[str] = None
    error_message: Optional[str] = None


class OperationListResponse(BaseModel):
    items: list[OperationLogResponse]
    total: int


class RollbackResponse(BaseModel):
    operation_id: int
    status: str
