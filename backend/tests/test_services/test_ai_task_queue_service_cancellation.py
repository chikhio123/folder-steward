import pytest
import threading
import time
from unittest.mock import MagicMock
from app.services.ai_task_queue_service import AITaskQueueService
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
