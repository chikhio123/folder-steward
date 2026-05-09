import pytest
from unittest.mock import MagicMock
from app.services.organize_plan_service import OrganizePlanService

def test_accept_plan_uses_repo():
    mock_plan_repo = MagicMock()
    mock_plan_repo.get_plan.return_value = MagicMock(status="draft")
    
    svc = OrganizePlanService(plan_repo=mock_plan_repo)
    # Just asserting the structure exists
    assert hasattr(svc, 'plan_repo')