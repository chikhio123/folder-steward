import pytest
from unittest.mock import MagicMock, patch
from app.services.extract_service import ExtractService
from app.models.file_record import FileRecord
from app.models.extract_task import ExtractTask
from app.models.file_content import FileContent
from app.models.scan_task import now_iso

def test_cleanup_ghost_tasks(monkeypatch):
    mock_conn = MagicMock()
    mock_get_connection = MagicMock(return_value=mock_conn)
    monkeypatch.setattr("app.services.extract_service.get_connection", mock_get_connection)

    mock_task_repo = MagicMock()
    mock_file_repo = MagicMock()
    mock_content_repo = MagicMock()

    monkeypatch.setattr("app.services.extract_service.ExtractTaskRepository", lambda: mock_task_repo)
    monkeypatch.setattr("app.services.extract_service.FileRepository", lambda: mock_file_repo)
    monkeypatch.setattr("app.services.extract_service.FileContentRepository", lambda: mock_content_repo)

    # Instantiate ExtractService
    svc = ExtractService()

    # Verify that cleanup was called
    assert mock_conn.execute.call_count >= 2
    executed_queries = [call.args[0] for call in mock_conn.execute.call_args_list]
    assert any("UPDATE extract_tasks SET status = 'failed'" in q for q in executed_queries)
    assert any("UPDATE file_contents SET extract_status = 'failed'" in q for q in executed_queries)

@patch("app.services.extract_service.get_connection")
@patch("app.services.extract_service.ExtractTaskRepository")
@patch("app.services.extract_service.FileRepository")
@patch("app.services.extract_service.FileContentRepository")
def test_create_extract_tasks(mock_content_repo, mock_file_repo, mock_task_repo, mock_get_conn):
    mock_conn = MagicMock()
    mock_get_conn.return_value = mock_conn

    # Mock the database returning one valid file record
    mock_conn.execute.return_value.fetchall.return_value = [{"id": 1, "extract_status": None, "extractor_type": None}]

    # Mock content_repo get_by_file_id returning None (no existing content)
    mock_content_repo_inst = MagicMock()
    mock_content_repo_inst.get_by_file_id.return_value = None
    mock_content_repo.return_value = mock_content_repo_inst

    # Mock task_repo create returning task ID 10
    mock_task_repo_inst = MagicMock()
    mock_task_repo_inst.create.return_value = 10
    mock_task_repo.return_value = mock_task_repo_inst

    svc = ExtractService()

    # Mock the executor to avoid actual threading
    mock_executor = MagicMock()
    svc._executor = mock_executor

    created, skipped = svc.create_extract_tasks(mode="missing_only")

    assert created == 1
    assert skipped == 0
    mock_executor.submit.assert_called_once_with(svc.run_extract_task, 10)
