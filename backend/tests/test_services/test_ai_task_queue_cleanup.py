import pytest
from unittest.mock import MagicMock
from app.services.ai_task_queue_service import AITaskQueueService

def test_cleanup_ghost_tasks_uses_repo():
    mock_repo = MagicMock()
    svc = AITaskQueueService()
    svc.task_repo = mock_repo
    svc._cleanup_ghost_tasks()
    mock_repo.cleanup_ghost_tasks.assert_called_once()
    mock_repo.resurrect_pending_tasks.assert_called_once()