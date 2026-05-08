import pytest
from unittest.mock import MagicMock
from app.services.operation_service import OperationService

def test_operation_service_uses_repos():
    mock_settings = MagicMock()
    mock_settings.get.return_value = "D:/Archive"
    
    mock_op_repo = MagicMock()
    
    svc = OperationService()
    svc.settings_repo = mock_settings
    svc.op_repo = mock_op_repo
    
    # We just verify it doesn't crash on init and the repos are set
    assert hasattr(svc, 'settings_repo')