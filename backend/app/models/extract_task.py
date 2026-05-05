from dataclasses import dataclass
from typing import Optional

@dataclass
class ExtractTask:
    id: Optional[int] = None
    file_id: int = 0
    status: str = "pending"
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str = ""
