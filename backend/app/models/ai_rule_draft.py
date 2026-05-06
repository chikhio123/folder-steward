from dataclasses import dataclass
from typing import Optional

@dataclass
class AIRuleDraft:
    id: Optional[int] = None
    user_prompt: str = ""
    name: str = ""
    rule_type: str = ""
    pattern: str = ""
    target_dir: str = ""
    action: str = ""
    priority: int = 90
    reason: Optional[str] = None
    confidence: float = 0.0
    status: str = "draft"
    validation_error: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None
