from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
import asyncio
import threading
from fastapi.concurrency import run_in_threadpool
from ..schemas.ai_rule_schema import CreateRuleDraftRequest, RuleDraftResponse, PreviewResponse
from ..services.ai_rule_draft_service import AIRuleDraftService
from ..dependencies import get_ai_rule_draft_service
from ..services.ai_task_queue_service import cancel_event_var

router = APIRouter(tags=["ai_rules"])

@router.post("/ai/rule-drafts", response_model=RuleDraftResponse)
async def create_rule_draft(
    request: Request,
    body: CreateRuleDraftRequest,
    draft_service: AIRuleDraftService = Depends(get_ai_rule_draft_service)
):
    cancel_event = threading.Event()

    async def watch_disconnect():
        while True:
            if await request.is_disconnected():
                cancel_event.set()
                break
            await asyncio.sleep(0.5)

    watcher_task = asyncio.create_task(watch_disconnect())
    token = cancel_event_var.set(cancel_event)

    try:
        draft_id = await run_in_threadpool(draft_service.generate_draft, body.prompt)
    finally:
        watcher_task.cancel()
        cancel_event_var.reset(token)

    draft = draft_service.draft_repo.get(draft_id)
    if not draft:
        raise HTTPException(status_code=500, detail="Failed to retrieve created draft")

    return RuleDraftResponse(
        draft_id=draft.id,
        name=draft.name,
        rule_type=draft.rule_type,
        pattern=draft.pattern,
        target_dir=draft.target_dir,
        action=draft.action,
        priority=draft.priority,
        reason=draft.reason,
        confidence=draft.confidence,
        status=draft.status,
        validation_error=draft.validation_error
    )

@router.get("/ai/rule-drafts/{draft_id}/preview", response_model=PreviewResponse)
def preview_rule_draft(
    draft_id: int,
    draft_service: AIRuleDraftService = Depends(get_ai_rule_draft_service)
):
    preview_data = draft_service.get_preview(draft_id)
    return PreviewResponse(**preview_data)

@router.post("/ai/rule-drafts/{draft_id}/accept")
def accept_rule_draft(
    draft_id: int,
    background_tasks: BackgroundTasks,
    draft_service: AIRuleDraftService = Depends(get_ai_rule_draft_service)
):
    try:
        rule = draft_service.accept_draft(draft_id, background_tasks)
        return {"status": "success", "rule_id": rule.id if rule else None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
