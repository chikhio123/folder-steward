from dataclasses import dataclass
from typing import Optional

@dataclass
class OrganizePlanItem:
    id: Optional[int] = None
    plan_id: int = 0
    file_id: int = 0
    source_path: str = ""
    target_dir: str = ""
    target_path: str = ""
    directory_status: str = "proposed_new"
    confidence: float = 0.0
    reason: Optional[str] = None
    evidence_json: Optional[str] = None
    status: str = "pending"
    created_at: str = ""
    updated_at: Optional[str] = None
