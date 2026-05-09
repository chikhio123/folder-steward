import pytest
from unittest.mock import MagicMock
from app.services.path_protection_service import PathProtectionService
from app.services.llm_provider_service import LLMProviderService

def test_path_protection_uses_repo():
    mock_repo = MagicMock()
    mock_repo.get.return_value = '["/mock/exclude"]'
    svc = PathProtectionService(settings_repo=mock_repo)
    paths = [p.replace('\\', '/') for p in svc.get_exclude_paths()]
    assert "D:/mock/exclude" in paths or "/mock/exclude" in paths
    mock_repo.get.assert_called_with(svc.SETTING_KEY)

def test_llm_provider_uses_repo():
    mock_repo = MagicMock()
    mock_repo.get_all.return_value = {"llm_model": "mock_model"}
    svc = LLMProviderService(settings_repo=mock_repo)
    settings = svc._get_settings()
    assert settings["model"] == "mock_model"
    mock_repo.get_all.assert_called_once()