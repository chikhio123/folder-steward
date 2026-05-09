import pytest
from unittest.mock import MagicMock, patch
from app.services.ai_task_queue_service import AITaskQueueService
from app.services.llm_provider_service import RateLimitException
from app.models.ai_task import AITask
from app.core.database import get_connection, init_db

@pytest.fixture(autouse=True)
def setup_ai_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM ai_tasks")
    conn.commit()

def test_enqueue_task():
    svc = AITaskQueueService()

    # Mock the executor to run handler synchronously for testing
    mock_executor = MagicMock()
    svc._executor = mock_executor

    task = AITask(task_type="classification", total_items=1)

    def mock_handler(t):
        t.processed_items = 1

    task_id = svc.enqueue_task(task, mock_handler)
    assert task_id > 0

    saved_task = svc.task_repo.get(task_id)
    assert saved_task.status == "pending"
    assert saved_task.task_type == "classification"

    # Verify submit was called
    mock_executor.submit.assert_called_once()

def test_task_rate_limit_retry():
    svc = AITaskQueueService()

    task = AITask(task_type="classification", total_items=1)
    task_id = svc.task_repo.create(task)

    # Handler throws RateLimitException
    def failing_handler(t):
        raise RateLimitException("429 Too Many Requests")

    # Mock the executor and rate_limiter
    mock_executor = MagicMock()
    svc._executor = mock_executor

    mock_rate_limiter = MagicMock()
    svc._rate_limiter = mock_rate_limiter

    svc._run_task_wrapper(task_id, failing_handler)

    updated_task = svc.task_repo.get(task_id)
    # It should have caught the exception and reset the task to pending
    assert updated_task.status == "pending"
    assert "Connection/Rate limit issue" in updated_task.error_message

    # Assert record_429 was called and it was re-submitted
    mock_rate_limiter.record_429.assert_called_once()
    mock_executor.submit.assert_called_once()

def test_task_failure():
    svc = AITaskQueueService()

    task = AITask(task_type="classification", total_items=1)
    task_id = svc.task_repo.create(task)

    def failing_handler(t):
        raise ValueError("Something went wrong")

    svc._run_task_wrapper(task_id, failing_handler)

    updated_task = svc.task_repo.get(task_id)
    assert updated_task.status == "failed"
    assert "Something went wrong" in updated_task.error_message
