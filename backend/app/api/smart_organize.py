from fastapi import APIRouter, HTTPException
from ..schemas.smart_organize_schema import (
    AIClassifyRequest, AIClassifyResponse,
    OrganizePlanRequest, OrganizePlanResponse,
    PlanPreviewResponse
)
from ..services.ai_classification_service import AIClassificationService
from ..services.organize_plan_service import OrganizePlanService
from ..services.ai_task_queue_service import AITaskQueueService
from ..models.ai_task import AITask
import json

router = APIRouter(tags=["smart_organize"])
class_service = AIClassificationService()
plan_service = OrganizePlanService()
queue_service = AITaskQueueService()

@router.post("/ai/classify", response_model=AIClassifyResponse)
def create_classification_tasks(body: AIClassifyRequest):
    if not body.file_ids:
        raise HTTPException(400, "No files specified")

    task = AITask(
        task_type="classification",
        total_items=len(body.file_ids),
        input_json=json.dumps({"file_ids": body.file_ids, "archive_root": body.archive_root})
    )

    def handler(t: AITask):
        inputs = json.loads(t.input_json)
        for fid in inputs["file_ids"]:
            class_service.process_classification_task(fid, inputs["archive_root"])
            t.processed_items += 1

    task_id = queue_service.enqueue_task(task, handler)

    return AIClassifyResponse(
        task_id=task_id,
        status="pending",
        queued_count=len(body.file_ids)
    )

@router.post("/ai/organize-plans", response_model=OrganizePlanResponse)
def create_organize_plan(body: OrganizePlanRequest):
    task = AITask(
        task_type="organize_plan",
        input_json=json.dumps({"scope": body.scope, "archive_root": body.archive_root, "min_confidence": body.min_confidence})
    )

    def handler(t: AITask):
        inputs = json.loads(t.input_json)
        plan_id = plan_service.generate_plan(inputs["scope"], inputs["archive_root"], inputs["min_confidence"])
        t.result_ref_id = plan_id
        t.result_ref_type = "organize_plan"

    task_id = queue_service.enqueue_task(task, handler)

    return OrganizePlanResponse(
        task_id=task_id,
        status="pending"
    )

@router.get("/ai/organize-plans/{plan_id}", response_model=PlanPreviewResponse)
def get_plan_preview(plan_id: int):
    data = plan_service.get_plan_preview(plan_id)
    if not data:
        raise HTTPException(404, "Plan not found")
    return PlanPreviewResponse(**data)

@router.post("/ai/organize-plans/{plan_id}/accept")
def accept_organize_plan(plan_id: int, archive_root: str):
    try:
        plan_service.accept_plan(plan_id, archive_root)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(400, str(e))
