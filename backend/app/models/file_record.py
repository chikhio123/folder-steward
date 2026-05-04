from dataclasses import dataclass
from typing import Optional


@dataclass
class FileRecord:
    id: Optional[int] = None
    original_path: str = ""
    current_path: str = ""
    filename: str = ""
    extension: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: int = 0
    sha256: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    indexed_at: str = ""
    status: str = "active"
    last_error: Optional[str] = None
