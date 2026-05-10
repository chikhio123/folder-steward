import json
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_settings_repository, get_ai_task_queue_service
from unittest.mock import MagicMock

client = TestClient(app)

def test_classify_uses_settings_repository():
    mock_settings = MagicMock()
    mock_settings.get.return_value = "D:/Archive"
    app.dependency_overrides[get_settings_repository] = lambda: mock_settings
    
    mock_queue = MagicMock()
    mock_queue.enqueue_task.return_value = 1
    app.dependency_overrides[get_ai_task_queue_service] = lambda: mock_queue

    response = client.post("/api/ai/classify", json={"file_ids": [1, 2]})
    
    assert response.status_code == 200
    mock_settings.get.assert_called_with("archive_root")
    app.dependency_overrides.clear()

def test_update_exclude_paths_uses_settings_repository():
    mock_settings = MagicMock()
    app.dependency_overrides[get_settings_repository] = lambda: mock_settings
    
    response = client.post("/api/ai/exclude-paths", json={"exclude_paths": ["/mock/path"]})
    
    assert response.status_code == 200
    mock_settings.set.assert_called_once()
    app.dependency_overrides.clear()