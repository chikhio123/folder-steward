from fastapi import APIRouter

from ..repositories.file_repository import FileRepository
from ..repositories.scan_task_repository import ScanTaskRepository
from ..repositories.operation_log_repository import OperationLogRepository
from ..repositories.suggestion_repository import SuggestionRepository

router = APIRouter(tags=["dashboard"])
file_repo = FileRepository()
task_repo = ScanTaskRepository()
op_repo = OperationLogRepository()
sug_repo = SuggestionRepository()


@router.get("/dashboard")
def get_dashboard():
    return {
        "total_files": file_repo.count(),
        "total_size": file_repo.total_size(),
        "duplicate_groups": file_repo.count_duplicate_groups(),
        "pending_suggestions": sug_repo.count_pending(),
        "recent_tasks": [
            {
                "task_id": t.id,
                "root_path": t.root_path,
                "status": t.status,
                "total_files": t.total_files,
                "scanned_files": t.scanned_files,
                "failed_files": t.failed_files,
                "created_at": t.created_at,
            }
            for t in task_repo.list_recent(5)
        ],
        "recent_operations": [
            {
                "id": o.id,
                "operation_type": o.operation_type,
                "source_path": o.source_path,
                "target_path": o.target_path,
                "status": o.status,
                "rollback_available": bool(o.rollback_available),
                "executed_at": o.executed_at,
            }
            for o in op_repo.list_recent(5)
        ],
    }
