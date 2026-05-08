from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class AIClassifyRequest(BaseModel):
    file_ids: List[int]

class AIClassifyResponse(BaseModel):
    task_id: int
    status: str
    queued_count: int

class OrganizePlanRequest(BaseModel):
    scope: str
    min_confidence: float = 0.65

class OrganizePlanResponse(BaseModel):
    task_id: int
    status: str

class PlanPreviewResponse(BaseModel):
    plan_id: int
    title: str
    status: str
    groups: Dict[str, Any]

class ExcludePathsRequest(BaseModel):
    exclude_paths: List[str]

class ExcludePathsResponse(BaseModel):
    status: str
    exclude_paths: List[str]
