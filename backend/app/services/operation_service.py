import shutil
from pathlib import Path

from ..core.database import get_connection
from ..core.errors import OperationError, PathSafetyError, RollbackError
from ..models.operation_log import OperationLog
from ..models.scan_task import now_iso
from ..repositories.file_repository import FileRepository
from ..repositories.operation_log_repository import OperationLogRepository
from ..repositories.suggestion_repository import SuggestionRepository
from .path_safety_service import PathSafetyService


class OperationService:
    def __init__(self) -> None:
        self.file_repo = FileRepository()
        self.sug_repo = SuggestionRepository()
        self.op_repo = OperationLogRepository()
        self.safety_service = PathSafetyService()

    def execute_suggestions(self, suggestion_ids: list[int]) -> dict:
        suggestions = self.sug_repo.list_by_ids(suggestion_ids)
        success_count = 0
        failed_count = 0
        results = []

        for sug in suggestions:
            try:
                # Pre-execution validation
                source = Path(sug.source_path)
                target = Path(sug.target_path)

                if not source.exists():
                    raise OperationError(f"Source file missing: {source}")

                target.parent.mkdir(parents=True, exist_ok=True)

                if target.exists():
                    sug.conflict_status = "target_exists"
                    self.sug_repo.update(sug)
                    raise OperationError(f"Target already exists: {target}")

                self.safety_service.validate_move(source, target)

                # Execute move
                shutil.move(str(source), str(target))

                # DB writes in a single transaction for atomicity
                conn = get_connection()
                conn.execute("BEGIN")
                try:
                    self.file_repo.update_path(sug.file_id, str(target))
                    op_id = self.op_repo.create(OperationLog(
                        operation_type="move",
                        file_id=sug.file_id,
                        source_path=sug.source_path,
                        target_path=str(target),
                        status="success",
                        rollback_available=1,
                        executed_at=now_iso(),
                    ))
                    self.sug_repo.update_status(sug.id, "executed")
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

                success_count += 1
                results.append({
                    "suggestion_id": sug.id,
                    "status": "success",
                    "operation_id": op_id,
                })

            except (OperationError, PathSafetyError, OSError, shutil.Error) as e:
                failed_count += 1
                self.sug_repo.update_status(sug.id, "failed")

                op_log = OperationLog(
                    operation_type="move",
                    file_id=sug.file_id,
                    source_path=sug.source_path,
                    target_path=sug.target_path,
                    status="failed",
                    rollback_available=0,
                    executed_at=now_iso(),
                    error_message=str(e),
                )
                self.op_repo.create(op_log)

                results.append({
                    "suggestion_id": sug.id,
                    "status": "failed",
                    "error_message": str(e),
                })

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        }

    def rollback_operation(self, operation_id: int) -> dict:
        op_log = self.op_repo.get(operation_id)
        if not op_log:
            raise RollbackError(f"Operation not found: {operation_id}")
        if not op_log.rollback_available:
            raise RollbackError(f"Operation {operation_id} is not rollback-available")
        if not op_log.target_path:
            raise RollbackError(f"Operation {operation_id} has no target path for rollback")

        source = Path(op_log.target_path)
        target = Path(op_log.source_path)

        if not source.exists():
            raise RollbackError(f"Rollback source not found: {source}")

        if target.exists():
            raise RollbackError(f"Rollback target already exists: {target}")

        # Validate paths before rolling back
        try:
            self.safety_service.validate_move(source, target)
        except PathSafetyError as e:
            raise RollbackError(f"Rollback path validation failed: {e}")

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))

            if op_log.file_id:
                self.file_repo.update_path(op_log.file_id, str(target))

            op_log.status = "rolled_back"
            op_log.rollback_available = 0
            op_log.rollback_at = now_iso()
            self.op_repo.update(op_log)

            # Record the rollback as its own log entry
            rollback_log = OperationLog(
                operation_type="rollback",
                file_id=op_log.file_id,
                source_path=op_log.target_path,
                target_path=op_log.source_path,
                status="success",
                rollback_available=0,
                executed_at=now_iso(),
            )
            self.op_repo.create(rollback_log)

            return {"operation_id": operation_id, "status": "rolled_back"}

        except OSError as e:
            raise RollbackError(f"Rollback failed: {e}")
