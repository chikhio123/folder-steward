from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel
from ..services.feedback_rule_service import FeedbackRuleService

router = APIRouter(tags=["feedback_rules"])
feedback_service = FeedbackRuleService()

class CreateDraftFromPatternRequest(BaseModel):
    target_dir: str
    keyword: str

@router.get("/ai/feedback-patterns")
def get_feedback_patterns() -> List[Dict[str, Any]]:
    return feedback_service.analyze_recent_operations()

@router.post("/ai/feedback-patterns/draft")
def create_draft_from_pattern(body: CreateDraftFromPatternRequest):
    draft_id = feedback_service.generate_draft_from_pattern(body.target_dir, body.keyword)
    return {"draft_id": draft_id, "status": "success"}
