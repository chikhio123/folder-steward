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

    # Instantiate ExtractService (doesn't call cleanup now)
    svc = ExtractService()

    # Call cleanup explicitly
    ExtractService.cleanup_ghost_tasks()

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

@patch("app.services.extract_service.ExtractTaskRepository")
@patch("app.services.extract_service.FileRepository")
@patch("app.services.extract_service.FileContentRepository")
@patch("app.services.extract_service.Path")
def test_extract_skips_file_over_size_limit(mock_path_cls, mock_content_repo, mock_file_repo, mock_task_repo):
    mock_task_repo_inst = MagicMock()
    mock_task_repo_inst.get.return_value = ExtractTask(id=1, file_id=1, status="pending")
    mock_task_repo.return_value = mock_task_repo_inst

    mock_file_repo_inst = MagicMock()
    mock_file_repo_inst.get.return_value = FileRecord(id=1, current_path="/fake.txt", extension=".txt", status="active")
    mock_file_repo.return_value = mock_file_repo_inst

    svc = ExtractService()
    svc.content_repo = MagicMock()

    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True

    mock_stat = MagicMock()
    from app.services.extract_limits import MAX_EXTRACT_FILE_MB
    mock_stat.st_size = (MAX_EXTRACT_FILE_MB + 1) * 1024 * 1024
    mock_path.stat.return_value = mock_stat

    mock_path_cls.return_value = mock_path

    svc.run_extract_task(1)

    updated_task = mock_task_repo_inst.update.call_args[0][0]
    assert updated_task.status == "failed"
    assert "exceeds limit" in updated_task.error_message

@patch("app.services.extract_service.ExtractTaskRepository")
@patch("app.services.extract_service.FileRepository")
@patch("app.services.extract_service.FileContentRepository")
@patch("app.services.extract_service.Path")
def test_extract_marks_missing_file_failed(mock_path_cls, mock_content_repo, mock_file_repo, mock_task_repo):
    mock_task_repo_inst = MagicMock()
    mock_task_repo_inst.get.return_value = ExtractTask(id=1, file_id=1, status="pending")
    mock_task_repo.return_value = mock_task_repo_inst

    mock_file_repo_inst = MagicMock()
    mock_file_repo_inst.get.return_value = FileRecord(id=1, current_path="/missing.txt", extension=".txt", status="active")
    mock_file_repo.return_value = mock_file_repo_inst

    svc = ExtractService()
    svc.content_repo = MagicMock()

    mock_path = MagicMock()
    mock_path.exists.return_value = False
    mock_path_cls.return_value = mock_path

    svc.run_extract_task(1)

    updated_task = mock_task_repo_inst.update.call_args[0][0]
    assert updated_task.status == "failed"
    assert "not found on disk" in updated_task.error_message

@patch("app.services.extract_service.ExtractTaskRepository")
@patch("app.services.extract_service.FileRepository")
@patch("app.services.extract_service.FileContentRepository")
@patch("app.services.extract_service.Path")
@patch("app.services.extract_service.get_extractor")
def test_extract_truncates_large_text(mock_get_extractor, mock_path_cls, mock_content_repo, mock_file_repo, mock_task_repo):
    mock_task_repo_inst = MagicMock()
    mock_task_repo_inst.get.return_value = ExtractTask(id=1, file_id=1, status="pending")
    mock_task_repo.return_value = mock_task_repo_inst

    mock_file_repo_inst = MagicMock()
    mock_file_repo_inst.get.return_value = FileRecord(id=1, current_path="/fake.txt", extension=".txt", status="active")
    mock_file_repo.return_value = mock_file_repo_inst

    svc = ExtractService()
    mock_content_repo_inst = MagicMock()
    svc.content_repo = mock_content_repo_inst

    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True

    mock_stat = MagicMock()
    mock_stat.st_size = 1024 # small enough
    mock_path.stat.return_value = mock_stat

    mock_path_cls.return_value = mock_path

    mock_extractor = MagicMock()
    mock_result = MagicMock()
    from app.services.extract_limits import MAX_TEXT_CHARS
    mock_result.text = "a" * (MAX_TEXT_CHARS + 100)
    mock_result.warnings = []
    mock_extractor.extract.return_value = mock_result
    mock_get_extractor.return_value = mock_extractor

    svc.run_extract_task(1)

    upsert_call = mock_content_repo_inst.upsert.call_args_list[-1]
    content = upsert_call[0][0]
    assert content.extract_status == "completed"
    assert content.text_length == MAX_TEXT_CHARS
    assert len(content.text_content) == MAX_TEXT_CHARS
    assert "truncated" in content.error_message

@patch("app.services.extract_service.ExtractTaskRepository")
@patch("app.services.extract_service.FileRepository")
@patch("app.services.extract_service.FileContentRepository")
@patch("app.services.extract_service.Path")
@patch("app.services.extract_service.get_extractor")
def test_extract_bad_extractor_exception_sets_failed(mock_get_extractor, mock_path_cls, mock_content_repo, mock_file_repo, mock_task_repo):
    mock_task_repo_inst = MagicMock()
    mock_task_repo_inst.get.return_value = ExtractTask(id=1, file_id=1, status="pending")
    mock_task_repo.return_value = mock_task_repo_inst

    mock_file_repo_inst = MagicMock()
    mock_file_repo_inst.get.return_value = FileRecord(id=1, current_path="/fake.txt", extension=".txt", status="active")
    mock_file_repo.return_value = mock_file_repo_inst

    svc = ExtractService()
    svc.content_repo = MagicMock()

    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_stat = MagicMock()
    mock_stat.st_size = 1024
    mock_path.stat.return_value = mock_stat
    mock_path_cls.return_value = mock_path

    mock_extractor = MagicMock()
    mock_extractor.extract.side_effect = Exception("corrupt file")
    mock_get_extractor.return_value = mock_extractor

    svc.run_extract_task(1)

    updated_task = mock_task_repo_inst.update.call_args[0][0]
    assert updated_task.status == "failed"
    assert "corrupt file" in updated_task.error_message
