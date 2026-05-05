from pydantic import BaseModel
from typing import Optional, List

class CreateExtractTasksRequest(BaseModel):
    file_ids: Optional[List[int]] = None
    mode: str = "missing_only"  # missing_only, failed_only, force

class CreateExtractTasksResponse(BaseModel):
    created_count: int
    skipped_count: int

class ExtractTaskResponse(BaseModel):
    id: int
    file_id: int
    status: str
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

class ExtractTaskListResponse(BaseModel):
    items: List[ExtractTaskResponse]
    total: int
