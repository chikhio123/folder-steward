import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_settings_repository
from unittest.mock import MagicMock

client = TestClient(app)

def test_settings_api_uses_dependency():
    mock_settings = MagicMock()
    mock_settings.get_all.return_value = {"archive_root": "D:/"}
    app.dependency_overrides[get_settings_repository] = lambda: mock_settings
    
    response = client.get("/api/settings")
    
    assert response.status_code == 200
    assert response.json() == {"archive_root": "D:/"}
    mock_settings.get_all.assert_called_once()
    app.dependency_overrides.clear()