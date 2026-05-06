from dataclasses import dataclass
from typing import Optional

@dataclass
class AIClassificationSuggestion:
    id: Optional[int] = None
    file_id: int = 0
    suggested_target_dir: str = ""
    directory_status: str = "proposed_new"
    confidence: float = 0.0
    reason: Optional[str] = None
    evidence_json: Optional[str] = None
    source_context_hash: Optional[str] = None
    status: str = "pending"
    created_at: str = ""
    updated_at: Optional[str] = None
