from dataclasses import dataclass
from typing import Optional

@dataclass
class OrganizePlan:
    id: Optional[int] = None
    title: str = ""
    scope: str = ""
    status: str = "draft"
    summary_json: Optional[str] = None
    created_at: str = ""
    updated_at: Optional[str] = None
