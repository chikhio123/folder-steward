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
        from ..repositories.settings_repository import SettingsRepository
        self.settings_repo = SettingsRepository()

    def _validate_target_within_archive(self, target_path: str, archive_root_str: str | None = None) -> None:
        if archive_root_str is None:
            archive_root_str = self.settings_repo.get("archive_root")
        if not archive_root_str:
            return  # no archive_root configured, skip check
        archive_root = Path(archive_root_str).resolve()
        target = Path(target_path).resolve()
        if not target.is_relative_to(archive_root):
            raise OperationError(
                f"Target path is outside archive root ({archive_root}): {target_path}"
            )

    def execute_suggestions(self, suggestion_ids: list[int]) -> dict:
        suggestions = self.sug_repo.list_by_ids(suggestion_ids)
        success_count = 0
        failed_count = 0
        results = []

        for sug in suggestions:
            op_id = None
            moved = False
            source = Path(sug.source_path)
            target = Path(sug.target_path)

            if sug.status not in ("pending", "accepted"):
                failed_count += 1
                results.append({
                    "suggestion_id": sug.id,
                    "status": "skipped",
                    "error_message": f"Suggestion status is {sug.status}"
                })
                continue

            try:
                # === Phase 1: Safety checks (no side effects) ===
                if not source.exists():
                    raise OperationError(f"Source file missing: {source}")

                if target.exists():
                    sug.conflict_status = "target_exists"
                    from ..core.uow import UnitOfWork
                    with UnitOfWork():
                        self.sug_repo.update(sug)
                    raise OperationError(f"Target already exists: {target}")

                if self.safety_service.is_system_sensitive_path(target):
                    raise OperationError(f"Target path is system-sensitive: {target}")

                self._validate_target_within_archive(str(target), sug.archive_root)

                # === Phase 2: Prepare target directory ===
                target.parent.mkdir(parents=True, exist_ok=True)

                # === Phase 3: Full move validation (includes writability check) ===
                self.safety_service.validate_move(source, target)

                # === Phase 4: Execute ===
                # 1. Create a pending operation log using self.op_repo.create
                op_log = OperationLog(
                    operation_type="move",
                    file_id=sug.file_id,
                    source_path=sug.source_path,
                    target_path=str(target),
                    status="pending",
                    rollback_available=0,
                    executed_at=now_iso(),
                )
                from ..core.uow import UnitOfWork
                with UnitOfWork():
                    op_id = self.op_repo.create(op_log)

                try:
                    shutil.move(str(source), str(target))
                    moved = True
                except Exception as e:
                    with UnitOfWork():
                        self.op_repo.mark_operation_failed(op_id, str(e))
                    raise

                try:
                    self.op_repo.commit_successful_move(op_id, sug.file_id, str(target), sug.id)
                except Exception as e:
                    if moved and target.exists() and not source.exists():
                        try:
                            shutil.move(str(target), str(source))
                            with UnitOfWork():
                                self.op_repo.mark_operation_failed(op_id, f"Database update failed (file reverted): {e}")
                        except Exception as rollback_err:
                            with UnitOfWork():
                                self.op_repo.mark_operation_failed(op_id, f"CRITICAL DESYNC! DB update failed ({e}) AND file revert failed ({rollback_err}). File is physically at {target} but DB thinks it is at {source}!")
                            raise OperationError(f"CRITICAL DESYNC: {rollback_err}") from e
                    else:
                        with UnitOfWork():
                            self.op_repo.mark_operation_failed(op_id, f"Database update failed: {e}")
                    raise OperationError(f"Database update failed after move: {e}") from e

                success_count += 1
                results.append({
                    "suggestion_id": sug.id,
                    "status": "success",
                    "operation_id": op_id,
                })

            except (OperationError, PathSafetyError, OSError, shutil.Error) as e:
                failed_count += 1
                from ..core.uow import UnitOfWork
                with UnitOfWork():
                    self.sug_repo.update_status(sug.id, "failed")

                if op_id is None:
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
                    try:
                        with UnitOfWork():
                            self.op_repo.create(op_log)
                    except Exception:
                        pass

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

        if self.safety_service.is_system_sensitive_path(target):
            raise RollbackError(f"Rollback target is system-sensitive: {target}")

        # Prepare then validate
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            self.safety_service.validate_move(source, target)
        except (OSError, PathSafetyError) as e:
            raise RollbackError(f"Rollback path validation failed: {e}")

        # Record the rollback as pending
        rollback_log = OperationLog(
            operation_type="rollback",
            file_id=op_log.file_id,
            source_path=op_log.target_path,
            target_path=op_log.source_path,
            status="pending",
            rollback_available=0,
            executed_at=now_iso(),
        )
        from ..core.uow import UnitOfWork
        with UnitOfWork():
            rollback_log_id = self.op_repo.create(rollback_log)

        moved = False
        try:
            shutil.move(str(source), str(target))
            moved = True
        except OSError as e:
            rollback_log.id = rollback_log_id
            rollback_log.status = "failed"
            rollback_log.error_message = str(e)
            with UnitOfWork():
                self.op_repo.update(rollback_log)
            raise RollbackError(f"Rollback failed: {e}")

        try:
            self.op_repo.commit_successful_rollback(operation_id, rollback_log_id, op_log.file_id, str(target))
        except Exception as e:
            if moved and target.exists() and not source.exists():
                shutil.move(str(target), str(source))

            rollback_log.id = rollback_log_id
            rollback_log.status = "failed"
            rollback_log.error_message = f"Database update failed: {e}"
            with UnitOfWork():
                self.op_repo.update(rollback_log)
            raise RollbackError(f"Database update failed after rollback: {e}") from e

        return {"operation_id": operation_id, "status": "rolled_back"}
