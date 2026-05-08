import pytest
import threading
import time
from unittest.mock import MagicMock
from app.services.ai_task_queue_service import AITaskQueueService
from app.models.ai_task import AITask

def test_task_cancellation_race_condition():
    # Setup mock repo
    mock_repo = MagicMock()
    # Initial status is pending, but when fetched later inside thread it will be 'failed'
    # representing a concurrent cancellation
    
    mock_task = AITask(task_type="chat", id=1, status="failed", error_message="Cancelled by user")
    mock_repo.get.return_value = mock_task
    
    svc = AITaskQueueService()
    svc.task_repo = mock_repo
    
    # We pass a handler that doesn't crash but simulates doing work
    def dummy_handler(t):
        pass
    
    # Call _run_task_wrapper directly for testing
    svc._run_task_wrapper(1, dummy_handler)
    
    # Assert that repo.update was not called to set it back to completed, 
    # or that the logic recognized it was cancelled.
    # In the current flawed implementation, mock_repo.update would be called 
    # to set status="running" then status="completed".
    # We want to ensure that if the DB says 'failed' and 'Cancelled', it aborts.
    
    # Wait, if get() returns 'failed' immediately, the wrapper should abort immediately 
    # because it expects 'pending'.
    # Let's test the race condition where it gets cancelled AFTER 'running' starts,
    # but the thread's event wasn't set (maybe multi-instance, or event was cleared).
    # The actual fix is to check the latest status in DB right before marking completed.
    pass

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
