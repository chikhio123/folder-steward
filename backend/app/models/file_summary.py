from dataclasses import dataclass
from typing import Optional

@dataclass
class FileSummary:
    id: Optional[int] = None
    file_id: int = 0
    summary: str = ""
    llm_provider: Optional[str] = None
    model_name: Optional[str] = None
    source_content_hash: Optional[str] = None
    status: str = "completed"
    error_message: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None
