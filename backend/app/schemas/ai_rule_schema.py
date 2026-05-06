from pydantic import BaseModel
from typing import Optional, List

class CreateRuleDraftRequest(BaseModel):
    prompt: str
    archive_root: str

class RuleDraftResponse(BaseModel):
    draft_id: int
    name: str
    rule_type: str
    pattern: str
    target_dir: str
    action: str
    priority: int
    reason: Optional[str] = None
    confidence: float
    status: str
    validation_error: Optional[str] = None

class PreviewItem(BaseModel):
    file_id: int
    filename: str
    current_path: str
    target_path: str
    reason: Optional[str] = None

class PreviewResponse(BaseModel):
    draft_id: int
    matched_count: int
    items: List[PreviewItem]
