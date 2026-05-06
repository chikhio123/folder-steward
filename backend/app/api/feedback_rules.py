from fastapi import APIRouter
import json
from typing import List, Dict, Any
from pydantic import BaseModel
from ..services.feedback_rule_service import FeedbackRuleService
from ..services.ai_task_queue_service import AITaskQueueService
from ..models.ai_task import AITask

router = APIRouter(tags=["feedback_rules"])
feedback_service = FeedbackRuleService()
queue_service = AITaskQueueService()

class CreateDraftFromPatternRequest(BaseModel):
    target_dir: str
    keyword: str

@router.get("/ai/feedback-patterns")
def get_feedback_patterns() -> List[Dict[str, Any]]:
    return feedback_service.analyze_recent_operations()

@router.post("/ai/feedback-patterns/draft")
def create_draft_from_pattern(body: CreateDraftFromPatternRequest):
    task = AITask(
        task_type="feedback_rule",
        total_items=1,
        input_json=json.dumps({"target_dir": body.target_dir, "keyword": body.keyword})
    )

    def handler(t: AITask):
        inputs = json.loads(t.input_json)
        draft_id = feedback_service.generate_draft_from_pattern(inputs["target_dir"], inputs["keyword"])
        t.result_ref_id = draft_id
        t.result_ref_type = "rule_draft"
        t.processed_items = 1

    task_id = queue_service.enqueue_task(task, handler)
    return {"task_id": task_id, "status": "pending"}
