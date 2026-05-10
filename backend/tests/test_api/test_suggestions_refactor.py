import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_settings_repository, get_suggestion_repository
from unittest.mock import MagicMock

client = TestClient(app)

def test_generate_suggestions_uses_saved_archive_root_when_body_missing():
    mock_settings = MagicMock()
    mock_settings.get.return_value = "D:/ArchiveFromSettings"
    app.dependency_overrides[get_settings_repository] = lambda: mock_settings
    
    mock_sug_repo = MagicMock()
    app.dependency_overrides[get_suggestion_repository] = lambda: mock_sug_repo
    
    with pytest.MonkeyPatch.context() as m:
        # Mock the SuggestionService to avoid executing actual logic
        from app.services.suggestion_service import SuggestionService
        mock_generate = MagicMock(return_value=(2, 0))
        m.setattr(SuggestionService, "generate_suggestions", mock_generate)
        
        response = client.post("/api/suggestions/generate", json={})
        
        assert response.status_code == 200
        mock_settings.get.assert_called_once_with("archive_root")
        mock_generate.assert_called_once_with("D:/ArchiveFromSettings")
    
    app.dependency_overrides.clear()