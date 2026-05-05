from dataclasses import dataclass
from typing import Optional

@dataclass
class Rule:
    id: Optional[int] = None
    name: str = ""
    rule_type: str = ""
    pattern: str = ""
    target_dir: Optional[str] = None
    action: str = ""
    priority: int = 100
    enabled: int = 1
    created_at: str = ""
    updated_at: Optional[str] = None
