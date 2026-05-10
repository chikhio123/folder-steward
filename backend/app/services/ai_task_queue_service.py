import threading
import contextvars
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional

from ..core.database import get_connection
from ..core.uow import UnitOfWork
from ..models.ai_task import AITask
from ..models.scan_task import now_iso
from ..repositories.ai_task_repository import AITaskRepository
from .ai_rate_limit_service import AIRateLimitService

cancel_event_var = contextvars.ContextVar('cancel_event', default=None)

class TaskCancelledException(Exception):
    pass

def raise_if_cancelled():
    """Raises TaskCancelledException if the current task has been cancelled."""
    event = cancel_event_var.get()
    if event and event.is_set():
        raise TaskCancelledException("Task was cancelled by user")

class AITaskQueueService:
    _executor = ThreadPoolExecutor(max_workers=2)  # Limited concurrency for LLMs
    _rate_limiter = AIRateLimitService()

    def __init__(self) -> None:
        self.task_repo = AITaskRepository()
        self._cancel_events: dict[int, threading.Event] = {}

    def cleanup_ghost_tasks(self) -> None:
        """Reset any 'running' tasks from a previous crashed run back to 'failed'."""
        with UnitOfWork():
            self.task_repo.cleanup_ghost_tasks()

    def _cleanup_ghost_tasks(self) -> None:
        self.cleanup_ghost_tasks()
        self._resurrect_pending_tasks()

    def _resurrect_pending_tasks(self) -> None:
        with UnitOfWork():
            self.task_repo.resurrect_pending_tasks()

    def enqueue_task(self, task: AITask, handler: Callable[[AITask], None]) -> int:
        """Adds an AI task to the database and submits it to the thread pool."""
        task.status = "pending"
        task.created_at = now_iso()
        with UnitOfWork():
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
        with UnitOfWork():
            self.task_repo.update(task)
        return True

    def _run_task_wrapper(self, task_id: int, handler: Callable[[AITask], None]) -> None:
        task = self.task_repo.get(task_id)
        if not task or task.status != "pending":
            return

        task.status = "running"
        task.started_at = now_iso()
        with UnitOfWork():
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
                with UnitOfWork():
                    self.task_repo.update(task)
                return

            # Double check database for concurrent cancellations (e.g. from another thread/process)
            latest_task = self.task_repo.get(task_id)
            if latest_task and latest_task.status == 'failed' and latest_task.error_message == 'Cancelled by user':
                return # Already cancelled in DB, don't overwrite with completed

            # Handler is expected to update result_ref_id, total_items, etc.
            task.status = "completed"
            task.finished_at = now_iso()
            with UnitOfWork():
                self.task_repo.update(task)
        except Exception as e:
            if cancel_event.is_set() or isinstance(e, TaskCancelledException) or "TaskCancelledException" in str(e):
                task.status = "failed"
                task.error_message = "Cancelled by user"
                task.finished_at = now_iso()
                with UnitOfWork():
                    self.task_repo.update(task)
                return

            from .llm_provider_service import RateLimitException
            is_retryable_error = (
                isinstance(e, RateLimitException) or
                "429" in str(e) or
                "disconnected" in str(e).lower() or
                "timed out" in str(e).lower() or
                "timeout" in str(e).lower() or
                "readerror" in str(e).lower()
            )
            if is_retryable_error:
                try:
                    latest_task = self.task_repo.get(task_id)
                    if latest_task and latest_task.status == 'failed' and latest_task.error_message == 'Cancelled by user':
                        return
                except Exception as db_e:
                    print(f"Warning: Failed to check latest task status during retry backoff: {db_e}")

                if isinstance(e, RateLimitException) or "429" in str(e):
                    self._rate_limiter.record_429()
                if task.retry_count < 3:
                    task.retry_count += 1
                    task.status = "pending"
                    task.error_message = f"Connection/Rate limit issue, retrying ({task.retry_count}/3). Last error: {e}"
                    task.finished_at = None
                    with UnitOfWork():
                        self.task_repo.update(task)
                    self._executor.submit(self._run_task_wrapper, task_id, handler)
                else:
                    task.status = "failed"
                    task.error_message = f"Max retries exceeded after connection/rate limit errors. Last error: {e}"
                    task.finished_at = now_iso()
                    with UnitOfWork():
                        self.task_repo.update(task)
            else:
                task.status = "failed"
                task.error_message = str(e)
                task.finished_at = now_iso()
                with UnitOfWork():
                    self.task_repo.update(task)
        finally:
            self._cancel_events.pop(task_id, None)
            cancel_event_var.reset(token)
