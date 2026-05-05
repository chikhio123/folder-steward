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

    @staticmethod
    def _validate_target_within_archive(target_path: str, archive_root_str: str | None = None) -> None:
        if archive_root_str is None:
            row = get_connection().execute(
                "SELECT value FROM app_settings WHERE key = 'archive_root'"
            ).fetchone()
            archive_root_str = row["value"] if row else None
        if not archive_root_str:
            return  # no archive_root configured, skip check
        archive_root = Path(archive_root_str).resolve()
        target = Path(target_path).resolve()
        if not target.is_relative_to(archive_root):
            raise OperationError(
                f"Target path is outside archive root ({archive_root}): {target_path}"
            )

    @staticmethod
    def _record_successful_move(conn, sug, target: Path) -> int:
        conn.execute(
            "UPDATE file_records SET current_path = ? WHERE id = ?",
            (str(target), sug.file_id),
        )
        cur = conn.execute(
            """INSERT INTO operation_logs
               (operation_type, file_id, source_path, target_path, status,
                rollback_available, executed_at, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("move", sug.file_id, sug.source_path, str(target), "success",
             1, now_iso(), None),
        )
        conn.execute(
            "UPDATE file_suggestions SET status=?, updated_at=? WHERE id=?",
            ("executed", now_iso(), sug.id),
        )
        return cur.lastrowid

    def execute_suggestions(self, suggestion_ids: list[int]) -> dict:
        suggestions = self.sug_repo.list_by_ids(suggestion_ids)
        success_count = 0
        failed_count = 0
        results = []

        for sug in suggestions:
            moved = False
            source = Path(sug.source_path)
            target = Path(sug.target_path)
            try:
                # === Phase 1: Safety checks (no side effects) ===
                if not source.exists():
                    raise OperationError(f"Source file missing: {source}")

                if target.exists():
                    sug.conflict_status = "target_exists"
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
                shutil.move(str(source), str(target))
                moved = True

                # DB writes in a single transaction for atomicity
                conn = get_connection()
                conn.execute("BEGIN")
                try:
                    op_id = self._record_successful_move(conn, sug, target)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    if moved and target.exists() and not source.exists():
                        shutil.move(str(target), str(source))
                    raise OperationError(f"Database update failed after move: {e}") from e

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
                try:
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

        try:
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
