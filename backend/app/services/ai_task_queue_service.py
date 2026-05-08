import threading
import contextvars
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

from ..core.database import get_connection
from ..models.ai_task import AITask
from ..models.scan_task import now_iso
from ..repositories.ai_task_repository import AITaskRepository
from .ai_rate_limit_service import AIRateLimitService

cancel_event_var = contextvars.ContextVar('cancel_event', default=None)

class AITaskQueueService:
    _executor = ThreadPoolExecutor(max_workers=2)  # Limited concurrency for LLMs
    _rate_limiter = AIRateLimitService()

    def __init__(self) -> None:
        self.task_repo = AITaskRepository()
        self._cancel_events: dict[int, threading.Event] = {}

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
        self._resurrect_pending_tasks()

    def _resurrect_pending_tasks(self) -> None:
        """Find pending tasks that were lost due to restart and submit them to thread pool."""
        conn = get_connection()
        rows = conn.execute("SELECT id FROM ai_tasks WHERE status = 'pending'").fetchall()
        # Handlers cannot be reliably resurrected because they are closures capturing scope
        # However, for simplicity in V3 M1-M12 we mark them failed if they don't have handlers.
        # A robust system would serialize the handler type. For now, mark them failed so they aren't stuck forever.
        for r in rows:
            conn.execute(
                "UPDATE ai_tasks SET status = 'failed', error_message = 'Lost handler due to process restart', finished_at = ? WHERE id = ?",
                (now_iso(), r["id"])
            )
        conn.commit()

    def enqueue_task(self, task: AITask, handler: Callable[[AITask], None]) -> int:
        """Adds an AI task to the database and submits it to the thread pool."""
        task.status = "pending"
        task.created_at = now_iso()
        task_id = self.task_repo.create(task)

        self._executor.submit(self._run_task_wrapper, task_id, handler)
        return task_id

    def cancel_task(self, task_id: int) -> bool:
        """Marks a task as cancelled in the database."""
        task = self.task_repo.get(task_id)
        if not task or task.status not in ("pending", "running"):
            return False

        if task_id in self._cancel_events:
            self._cancel_events[task_id].set()

        task.status = "failed"
        task.error_message = "Cancelled by user"
        task.finished_at = now_iso()
        self.task_repo.update(task)
        return True

    def _run_task_wrapper(self, task_id: int, handler: Callable[[AITask], None]) -> None:
        task = self.task_repo.get(task_id)
        if not task or task.status != "pending":
            return

        task.status = "running"
        task.started_at = now_iso()
        self.task_repo.update(task)

        cancel_event = threading.Event()
        self._cancel_events[task_id] = cancel_event
        token = cancel_event_var.set(cancel_event)

        try:
            # Respect rate limit
            is_interactive = task.task_type in ("chat", "rule_draft", "organize_plan", "classification")
            self._rate_limiter.wait_if_needed(is_interactive)

            # Execute the actual LLM logic via the passed handler
            handler(task)

            # Check if task was cancelled before marking completed
            if cancel_event.is_set():
                task.status = "failed"
                task.error_message = "Cancelled by user"
                task.finished_at = now_iso()
                self.task_repo.update(task)
                return

            # Handler is expected to update result_ref_id, total_items, etc.
            task.status = "completed"
            task.finished_at = now_iso()
            self.task_repo.update(task)
        except Exception as e:
            if cancel_event.is_set() or "TaskCancelledException" in str(e):
                task.status = "failed"
                task.error_message = "Cancelled by user"
                task.finished_at = now_iso()
                self.task_repo.update(task)
                return

            from .llm_provider_service import RateLimitException
            if isinstance(e, RateLimitException) or "429" in str(e):
                self._rate_limiter.record_429()
                if task.retry_count < 3:
                    task.retry_count += 1
                    task.status = "pending"
                    task.error_message = f"Rate limited, retrying ({task.retry_count}/3). Last error: {e}"
                    task.finished_at = None
                    self.task_repo.update(task)
                    self._executor.submit(self._run_task_wrapper, task_id, handler)
                else:
                    task.status = "failed"
                    task.error_message = f"Max retries exceeded after 429. Last error: {e}"
                    task.finished_at = now_iso()
                    self.task_repo.update(task)
            else:
                task.status = "failed"
                task.error_message = str(e)
                task.finished_at = now_iso()
                self.task_repo.update(task)
        finally:
            self._cancel_events.pop(task_id, None)
            cancel_event_var.reset(token)
