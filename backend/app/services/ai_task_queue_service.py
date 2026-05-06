import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

from ..core.database import get_connection
from ..models.ai_task import AITask
from ..models.scan_task import now_iso
from ..repositories.ai_task_repository import AITaskRepository
from .ai_rate_limit_service import AIRateLimitService

class AITaskQueueService:
    _executor = ThreadPoolExecutor(max_workers=2)  # Limited concurrency for LLMs
    _rate_limiter = AIRateLimitService()

    def __init__(self) -> None:
        self.task_repo = AITaskRepository()
        self._cleanup_ghost_tasks()

    @staticmethod
    def cleanup_ghost_tasks() -> None:
        """Reset any 'running' tasks from a previous crashed run back to 'failed'."""
        conn = get_connection()
        conn.execute(
            "UPDATE ai_tasks SET status = 'failed', error_message = 'Process terminated unexpectedly', finished_at = ? WHERE status = 'running'",
            (now_iso(),)
        )
        conn.commit()

    def _cleanup_ghost_tasks(self) -> None:
        self.cleanup_ghost_tasks()

    def enqueue_task(self, task: AITask, handler: Callable[[AITask], None]) -> int:
        """Adds an AI task to the database and submits it to the thread pool."""
        task.status = "pending"
        task.created_at = now_iso()
        task_id = self.task_repo.create(task)

        self._executor.submit(self._run_task_wrapper, task_id, handler)
        return task_id

    def _run_task_wrapper(self, task_id: int, handler: Callable[[AITask], None]) -> None:
        task = self.task_repo.get(task_id)
        if not task or task.status != "pending":
            return

        task.status = "running"
        task.started_at = now_iso()
        self.task_repo.update(task)

        try:
            # Respect rate limit
            self._rate_limiter.wait_if_needed()

            # Execute the actual LLM logic via the passed handler
            handler(task)

            # Handler is expected to update result_ref_id, total_items, etc.
            task.status = "completed"
            task.finished_at = now_iso()
            self.task_repo.update(task)
        except Exception as e:
            # If 429 occurs, handler could raise a specific exception that we catch here
            if "429" in str(e):
                self._rate_limiter.record_429()
                task.status = "rate_limited"
            else:
                task.status = "failed"
            task.error_message = str(e)
            task.finished_at = now_iso()
            self.task_repo.update(task)
