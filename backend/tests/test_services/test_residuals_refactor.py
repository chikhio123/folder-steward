import pytest
from unittest.mock import MagicMock
from app.services.organize_plan_service import OrganizePlanService
from app.models.organize_plan import OrganizePlan
from app.models.organize_plan_item import OrganizePlanItem

def test_accept_plan_uses_repo():
    mock_plan_repo = MagicMock()
    mock_plan_repo.get_plan.return_value = OrganizePlan(id=1, title="Test", scope="all", status="draft")
    
    mock_item = OrganizePlanItem(
        plan_id=1, file_id=10, ai_suggestion_id=100, source_path="A.txt", 
        target_dir="B", target_path="D:/B/A.txt", directory_status="existing", 
        confidence=0.9, status="pending"
    )
    mock_plan_repo.get_items_by_plan.return_value = [mock_item]
    
    mock_settings_repo = MagicMock()
    mock_settings_repo.get.return_value = "D:/Archive"
    
    mock_sug_repo = MagicMock()
    mock_ai_sug_repo = MagicMock()
    
    svc = OrganizePlanService(
        plan_repo=mock_plan_repo,
        settings_repo=mock_settings_repo,
        suggestion_repo=mock_sug_repo,
        class_repo=mock_ai_sug_repo
    )
    
    svc.accept_plan(1)
    
    # Assertions for the state chain
    mock_sug_repo.create.assert_called_once()
    mock_plan_repo.mark_items_converted.assert_called_once_with([None]) # item ID is None because we didn't mock it, but testing the call
    mock_ai_sug_repo.update_status_batch.assert_called_once_with([100], "converted")
    mock_plan_repo.update_plan.assert_called_once()

def test_reject_plan_uses_repo():
    mock_plan_repo = MagicMock()
    mock_plan_repo.get_plan.return_value = OrganizePlan(id=1, title="Test", scope="all", status="draft")
    
    mock_item = OrganizePlanItem(
        plan_id=1, file_id=10, ai_suggestion_id=100, source_path="A.txt", 
        target_dir="B", target_path="D:/B/A.txt", directory_status="existing", 
        confidence=0.9, status="pending"
    )
    mock_item.id = 55
    mock_plan_repo.get_items_by_plan.return_value = [mock_item]
    
    mock_ai_sug_repo = MagicMock()
    
    svc = OrganizePlanService(
        plan_repo=mock_plan_repo,
        class_repo=mock_ai_sug_repo
    )
    
    svc.reject_plan(1)
    
    mock_plan_repo.mark_items_rejected.assert_called_once_with([55])
    mock_ai_sug_repo.update_status_batch.assert_called_once_with([100], "pending")
    mock_plan_repo.update_plan.assert_called_once()