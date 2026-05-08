from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_file_repository
from unittest.mock import MagicMock

client = TestClient(app)

def test_list_files_uses_dependency():
    mock_repo = MagicMock()
    mock_repo.list_paginated.return_value = ([], 0)
    app.dependency_overrides[get_file_repository] = lambda: mock_repo
    
    response = client.get("/api/files")
    
    assert response.status_code == 200
    mock_repo.list_paginated.assert_called_once()
    app.dependency_overrides.clear()