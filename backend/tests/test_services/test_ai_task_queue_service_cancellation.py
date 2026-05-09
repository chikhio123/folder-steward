import pytest
import threading
import time
from unittest.mock import MagicMock
from app.services.ai_task_queue_service import AITaskQueueService, raise_if_cancelled, TaskCancelledException
from app.models.ai_task import AITask

def test_task_already_cancelled_before_running_is_not_updated():
    mock_repo = MagicMock()
    mock_repo.get.return_value = AITask(
        task_type="chat",
        id=1,
        status="failed",
        error_message="Cancelled by user",
    )

    svc = AITaskQueueService()
    svc.task_repo = mock_repo

    svc._run_task_wrapper(1, lambda t: None)

    mock_repo.update.assert_not_called()

def test_task_cancellation_pre_completion_check():
    mock_repo = MagicMock()
    mock_task_instance = AITask(task_type="chat", id=1, status="pending")

    def side_effect_get(task_id):
        # First call returns pending, second call returns failed
        if mock_repo.get.call_count == 1:
            return mock_task_instance
        else:
            return AITask(task_type="chat", id=1, status="failed", error_message="Cancelled by user")

    mock_repo.get.side_effect = side_effect_get

    svc = AITaskQueueService()
    svc.task_repo = mock_repo

    def dummy_handler(t):
        pass

    svc._run_task_wrapper(1, dummy_handler)

    # Check that update was NOT called with status="completed"
    for call in mock_repo.update.call_args_list:
        task_arg = call[0][0]
        assert task_arg.status != "completed"

def test_raise_if_cancelled_during_handler():
    mock_repo = MagicMock()
    mock_repo.get.return_value = AITask(task_type="chat", id=1, status="pending")

    svc = AITaskQueueService()
    svc.task_repo = mock_repo

    def handler_that_checks_cancellation(t):
        # Simulate an external thread cancelling the task
        svc.cancel_task(1)
        raise_if_cancelled()
        # Should not reach here
        t.processed_items = 100

    svc._run_task_wrapper(1, handler_that_checks_cancellation)

    # Verify that the task wasn't marked completed and processed_items wasn't updated
    updated_calls = [call[0][0] for call in mock_repo.update.call_args_list]
    # The last update should be a failure because of cancellation
    last_update = updated_calls[-1]
    assert last_update.status == "failed"
    assert "Cancelled by user" in last_update.error_message
    assert last_update.processed_items == 0

def test_retryable_error_does_not_override_cancelled_in_db():
    mock_repo = MagicMock()
    mock_task_instance = AITask(task_type="classification", id=1, status="pending")

    def side_effect_get(task_id):
        if mock_repo.get.call_count == 1:
            return mock_task_instance
        else:
            return AITask(task_type="classification", id=1, status="failed", error_message="Cancelled by user")

    mock_repo.get.side_effect = side_effect_get

    svc = AITaskQueueService()
    svc.task_repo = mock_repo

    # Mock the executor
    mock_executor = MagicMock()
    svc._executor = mock_executor

    def handler_that_raises_retryable(t):
        from app.services.llm_provider_service import RateLimitException
        raise RateLimitException("429 Too Many Requests")

    svc._run_task_wrapper(1, handler_that_raises_retryable)

    # Should not resubmit because it was cancelled in DB
    mock_executor.submit.assert_not_called()

    # Should not have called update to set status back to pending
    for call in mock_repo.update.call_args_list:
        task_arg = call[0][0]
        assert task_arg.status != "pending"
