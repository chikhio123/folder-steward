from fastapi import APIRouter, HTTPException
from ..schemas.smart_organize_schema import (
    AIClassifyRequest, AIClassifyResponse,
    OrganizePlanRequest, OrganizePlanResponse,
    PlanPreviewResponse, ExcludePathsRequest, ExcludePathsResponse
)
from ..services.ai_classification_service import AIClassificationService
from ..services.organize_plan_service import OrganizePlanService
from ..services.path_protection_service import PathProtectionService
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

    from ..core.database import get_connection
    conn = get_connection()
    row = conn.execute("SELECT value FROM app_settings WHERE key = 'archive_root'").fetchone()
    archive_root = row["value"] if row else ""

    if not archive_root:
        raise HTTPException(400, "archive_root is not configured in settings")

    task = AITask(
        task_type="classification",
        total_items=len(body.file_ids),
        input_json=json.dumps({"file_ids": body.file_ids, "archive_root": archive_root})
    )

    def handler(t: AITask):
        inputs = json.loads(t.input_json)
        file_ids = inputs["file_ids"]
        # 过滤排除目录（防线1：/ai/classify 入口）
        path_protection = PathProtectionService()
        file_ids, skipped = path_protection.filter_file_ids(file_ids)
        if skipped > 0:
            print(f"Skipped {skipped} files due to AI exclude paths")
        if not file_ids:
            raise ValueError("应用 AI 排除目录后，没有可处理的文件。")
        # 更新任务总数（过滤后）
        t.total_items = len(file_ids)
        class_service.process_classification_batch(
            file_ids,
            inputs["archive_root"],
            batch_size=30,
            task=t
        )

    task_id = queue_service.enqueue_task(task, handler)

    return AIClassifyResponse(
        task_id=task_id,
        status="pending",
        queued_count=len(body.file_ids)
    )

@router.get("/ai/tasks/{task_id}")
def get_ai_task(task_id: int):
    task = queue_service.task_repo.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task

@router.post("/ai/organize-plans", response_model=OrganizePlanResponse)
def create_organize_plan(body: OrganizePlanRequest):
    task = AITask(
        task_type="organize_plan",
        input_json=json.dumps({"scope": body.scope, "min_confidence": body.min_confidence})
    )

    def handler(t: AITask):
        inputs = json.loads(t.input_json)
        plan_id = plan_service.generate_plan(inputs["scope"], inputs["min_confidence"], task=t)
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
def accept_organize_plan(plan_id: int):
    try:
        plan_service.accept_plan(plan_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/ai/organize-plans/{plan_id}/reject")
def reject_organize_plan(plan_id: int):
    try:
        plan_service.reject_plan(plan_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/ai/exclude-paths")
def get_exclude_paths():
    service = PathProtectionService()
    return {"exclude_paths": service.get_exclude_paths()}

@router.post("/ai/exclude-paths", response_model=ExcludePathsResponse)
def update_exclude_paths(body: ExcludePathsRequest):
    paths = body.exclude_paths
    if not isinstance(paths, list):
        raise HTTPException(400, "exclude_paths must be an array")
    service = PathProtectionService()
    normalized = [service.normalize_path(p) for p in paths if isinstance(p, str) and p.strip()]

    import json
    from ..core.database import get_connection
    from ..models.scan_task import now_iso
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
        (service.SETTING_KEY, json.dumps(normalized), now_iso())
    )
    conn.commit()
    return ExcludePathsResponse(status="success", exclude_paths=normalized)
