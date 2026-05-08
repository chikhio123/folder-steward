import pytest
from unittest.mock import MagicMock
from app.services.organize_plan_service import OrganizePlanService

def test_generate_plan_uses_repositories():
    mock_settings = MagicMock()
    mock_settings.get.return_value = "D:/Archive"
    
    mock_file_repo = MagicMock()
    mock_file_repo.get_all_active_ids.return_value = [1, 2]
    
    mock_class_repo = MagicMock()
    mock_class_repo.get_pending_with_paths.return_value = []
    
    mock_path_prot = MagicMock()
    mock_path_prot.filter_file_ids.return_value = ([1, 2], 0)
    
    mock_class_svc = MagicMock()
    
    svc = OrganizePlanService(
        class_repo=mock_class_repo,
        path_protection=mock_path_prot,
        classification_service=mock_class_svc,
        settings_repo=mock_settings,
        file_repo=mock_file_repo
    )
    
    try:
        svc.generate_plan(scope="all")
    except ValueError:
        pass # Expected since get_pending_with_paths returns []
        
    mock_settings.get.assert_called_with("archive_root")
    mock_file_repo.get_all_active_ids.assert_called_once()
    mock_class_repo.delete_pending_by_files.assert_called_once_with([1, 2])