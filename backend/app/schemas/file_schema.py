from pydantic import BaseModel
from typing import Optional


class FileRecordResponse(BaseModel):
    id: int
    filename: str
    original_path: str
    current_path: str
    extension: Optional[str] = None
    size_bytes: int
    sha256: Optional[str] = None
    modified_at: Optional[str] = None
    status: str


class FileListResponse(BaseModel):
    items: list[FileRecordResponse]
    total: int
