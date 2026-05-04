from pydantic import BaseModel
from typing import Optional


class CreateScanTaskRequest(BaseModel):
    root_path: str


class ScanTaskResponse(BaseModel):
    task_id: int
    root_path: str
    status: str
    total_files: int
    scanned_files: int
    failed_files: int
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str


class ScanErrorItem(BaseModel):
    file_path: str
    error_message: str


class ScanErrorListResponse(BaseModel):
    items: list[ScanErrorItem]
