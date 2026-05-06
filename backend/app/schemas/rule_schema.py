from pydantic import BaseModel
from typing import Optional, List

class RuleCreateRequest(BaseModel):
    name: str
    rule_type: str
    pattern: str
    target_dir: Optional[str] = None
    action: str = "move_to"
    priority: int = 100
    enabled: int = 1

class RuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[str] = None
    pattern: Optional[str] = None
    target_dir: Optional[str] = None
    action: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[int] = None

class RuleResponse(BaseModel):
    id: int
    name: str
    rule_type: str
    pattern: str
    target_dir: Optional[str] = None
    action: str
    priority: int
    enabled: int
    created_at: str
    updated_at: Optional[str] = None
