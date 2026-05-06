from dataclasses import dataclass
from typing import Optional

@dataclass
class AITask:
    id: Optional[int] = None
    task_type: str = ""
    status: str = "pending"
    input_json: Optional[str] = None
    result_ref_type: Optional[str] = None
    result_ref_id: Optional[int] = None
    total_items: int = 0
    processed_items: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    estimated_tokens: int = 0
    actual_tokens: int = 0
    estimated_cost: float = 0.0
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None
