from dataclasses import dataclass
from typing import Optional


@dataclass
class OperationLog:
    id: Optional[int] = None
    operation_type: str = ""
    file_id: Optional[int] = None
    source_path: str = ""
    target_path: Optional[str] = None
    status: str = "success"
    rollback_available: int = 1
    executed_at: str = ""
    rollback_at: Optional[str] = None
    error_message: Optional[str] = None
