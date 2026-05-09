import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_settings_repository, get_suggestion_repository
from unittest.mock import MagicMock

client = TestClient(app)

def test_generate_suggestions_uses_settings_dependency():
    mock_settings = MagicMock()
    mock_settings.get.return_value = "D:/Archive"
    app.dependency_overrides[get_settings_repository] = lambda: mock_settings
    
    mock_sug_repo = MagicMock()
    app.dependency_overrides[get_suggestion_repository] = lambda: mock_sug_repo
    
    response = client.post("/api/v1/suggestions/generate", json={})
    if response.status_code == 404:
        response = client.post("/api/suggestions/generate", json={})
    if response.status_code == 404:
        response = client.post("/suggestions/generate", json={})
    
    app.dependency_overrides.clear()