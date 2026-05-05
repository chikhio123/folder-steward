from fastapi import APIRouter, HTTPException

from ..schemas.scan_task_schema import (
    CreateScanTaskRequest,
    ScanTaskResponse,
    ScanErrorItem,
    ScanErrorListResponse,
)
from ..services.scan_service import ScanService
from ..core.errors import PathSafetyError

router = APIRouter(tags=["scan-tasks"])
scan_service = ScanService()


@router.post("/scan-tasks", response_model=ScanTaskResponse)
def create_scan_task(body: CreateScanTaskRequest):
    try:
        task = scan_service.create_scan_task(body.root_path)
    except PathSafetyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ScanTaskResponse(
        task_id=task.id,
        root_path=task.root_path,
        status=task.status,
        total_files=task.total_files,
        scanned_files=task.scanned_files,
        failed_files=task.failed_files,
        error_message=task.error_message,
        started_at=task.started_at,
        finished_at=task.finished_at,
        created_at=task.created_at,
    )


@router.get("/scan-tasks/{task_id}", response_model=ScanTaskResponse)
def get_scan_task(task_id: int):
    task = scan_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return ScanTaskResponse(
        task_id=task.id,
        root_path=task.root_path,
        status=task.status,
        total_files=task.total_files,
        scanned_files=task.scanned_files,
        failed_files=task.failed_files,
        error_message=task.error_message,
        started_at=task.started_at,
        finished_at=task.finished_at,
        created_at=task.created_at,
    )


@router.post("/scan-tasks/{task_id}/cancel")
def cancel_scan_task(task_id: int):
    ok = scan_service.cancel_task(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled (not running or not found)")
    return {"task_id": task_id, "status": "cancelled"}


@router.get("/scan-tasks/{task_id}/errors", response_model=ScanErrorListResponse)
def get_scan_errors(task_id: int):
    errors = scan_service.get_errors(task_id)
    return ScanErrorListResponse(
        items=[ScanErrorItem(file_path=e.file_path, error_message=e.error_message) for e in errors]
    )
