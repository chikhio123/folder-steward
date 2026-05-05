from dataclasses import dataclass
from typing import Optional


@dataclass
class FileSuggestion:
    id: Optional[int] = None
    file_id: int = 0
    suggestion_type: str = "move"
    source_path: str = ""
    target_path: str = ""
    reason: Optional[str] = None
    confidence: float = 0.0
    conflict_status: str = "none"
    status: str = "pending"
    archive_root: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None
