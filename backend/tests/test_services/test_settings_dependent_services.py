import pytest
from unittest.mock import MagicMock
from app.services.path_protection_service import PathProtectionService
from app.services.llm_provider_service import LLMProviderService

def test_path_protection_uses_repo():
    mock_settings_repo = MagicMock()
    mock_settings_repo.get.return_value = '["/mock/exclude"]'
    
    mock_file_repo = MagicMock()
    mock_file_repo.get_paths_by_ids.return_value = [
        {"id": 1, "current_path": "/mock/exclude/file1.txt"},
        {"id": 2, "current_path": "/mock/keep/file2.txt"},
        {"id": 3, "current_path": None}
    ]
    
    svc = PathProtectionService(settings_repo=mock_settings_repo, file_repo=mock_file_repo)
    paths = [p.replace('\\', '/') for p in svc.get_exclude_paths()]
    assert "D:/mock/exclude" in paths or "/mock/exclude" in paths
    mock_settings_repo.get.assert_called_with(svc.SETTING_KEY)
    
    valid_ids, skipped = svc.filter_file_ids([1, 2, 3])
    assert skipped == 1
    assert valid_ids == [2, 3]  # order preserved based on mock logic
    mock_file_repo.get_paths_by_ids.assert_called_once_with([1, 2, 3])

def test_llm_provider_uses_repo():
    mock_repo = MagicMock()
    mock_repo.get_all.return_value = {"llm_model": "mock_model"}
    svc = LLMProviderService(settings_repo=mock_repo)
    settings = svc._get_settings()
    assert settings["model"] == "mock_model"
    mock_repo.get_all.assert_called_once()