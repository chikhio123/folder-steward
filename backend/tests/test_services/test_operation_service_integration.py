import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.core.database import init_db, get_connection
from app.core.uow import UnitOfWork
from app.core.errors import OperationError, RollbackError
from app.models.file_record import FileRecord
from app.models.file_suggestion import FileSuggestion
from app.models.scan_task import now_iso
from app.services.operation_service import OperationService

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    tables = [
        "file_suggestions", "operation_logs",
        "file_records", "app_settings"
    ]
    for t in tables:
        conn.execute(f"DELETE FROM {t}")
    conn.commit()

@pytest.fixture(autouse=True)
def mock_safety():
    with patch("app.services.path_safety_service.PathSafetyService.is_system_sensitive_path", return_value=False):
        yield

@pytest.fixture
def tmp_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_root = Path(tmpdir) / "Archive"
        archive_root.mkdir()

        conn = get_connection()
        conn.execute("INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)", ("archive_root", str(archive_root), now_iso()))
        conn.commit()

        yield Path(tmpdir), archive_root

@pytest.fixture
def op_service():
    return OperationService()

def create_mock_file(path: Path, content: str = "test"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def test_execute_target_already_exists(op_service, tmp_workspace):
    tmpdir, archive_root = tmp_workspace

    source = tmpdir / "source.txt"
    target = archive_root / "target.txt"
    create_mock_file(source)
    create_mock_file(target) # Target exists!

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="source.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)

    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])

    assert res["success_count"] == 0
    assert res["failed_count"] == 1

    # Assert physical files
    assert source.exists()
    assert target.exists()

    # Assert DB
    sug_db = op_service.sug_repo.get(sug_id)
    assert sug_db.status == "failed"
    assert sug_db.conflict_status == "target_exists"

    rec_db = op_service.file_repo.get(file_id)
    assert rec_db.current_path == str(source) # Unchanged

def test_execute_source_missing(op_service, tmp_workspace):
    tmpdir, archive_root = tmp_workspace
    source = tmpdir / "missing.txt"
    target = archive_root / "target.txt"

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="missing.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)

    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])
    assert res["success_count"] == 0
    assert res["failed_count"] == 1

    sug_db = op_service.sug_repo.get(sug_id)
    assert sug_db.status == "failed"
    assert "missing" in res["results"][0]["error_message"].lower()

    ops, _ = op_service.op_repo.list_paginated()
    assert any(op.status == "failed" and op.file_id == file_id for op in ops)

def test_execute_target_outside_archive_root(op_service, tmp_workspace):
    tmpdir, archive_root = tmp_workspace
    source = tmpdir / "source.txt"
    target = tmpdir / "outside" / "target.txt" # Outside archive_root
    create_mock_file(source)

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="source.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)

    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])
    assert res["success_count"] == 0
    assert res["failed_count"] == 1

    sug_db = op_service.sug_repo.get(sug_id)
    assert sug_db.status == "failed"
    assert "outside" in res["results"][0]["error_message"].lower()

    ops, _ = op_service.op_repo.list_paginated()
    assert any(op.status == "failed" and op.file_id == file_id for op in ops)

@patch("app.services.path_safety_service.PathSafetyService.is_system_sensitive_path", return_value=True)
def test_execute_target_system_sensitive_path(mock_is_sensitive, op_service, tmp_workspace):
    tmpdir, archive_root = tmp_workspace
    source = tmpdir / "source.txt"
    target = archive_root / "windows" / "system32" / "target.txt"
    create_mock_file(source)

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="source.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)

    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])
    assert res["success_count"] == 0

    assert source.exists()
    assert not target.exists()
    sug_db = op_service.sug_repo.get(sug_id)
    assert sug_db.status == "failed"

    ops, _ = op_service.op_repo.list_paginated()
    assert any(op.status == "failed" and op.file_id == file_id for op in ops)

@patch("app.repositories.operation_log_repository.OperationLogRepository.commit_successful_move")
def test_execute_db_update_fails_rollback_file(mock_commit_db, op_service, tmp_workspace):
    mock_commit_db.side_effect = Exception("Simulated DB commit error")

    tmpdir, archive_root = tmp_workspace
    source = tmpdir / "source.txt"
    target = archive_root / "target.txt"
    create_mock_file(source)

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="source.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)

    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])
    assert res["failed_count"] == 1

    # Assert physical files MUST BE REVERTED
    assert source.exists()
    assert not target.exists()

    sug_db = op_service.sug_repo.get(sug_id)
    assert sug_db.status == "failed"

def test_rollback_success(op_service, tmp_workspace):
    tmpdir, archive_root = tmp_workspace
    source = tmpdir / "source.txt"
    target = archive_root / "target.txt"
    create_mock_file(source)

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="source.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)

    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])
    assert res["success_count"] == 1, str(res)
    op_id = res["results"][0]["operation_id"]

    assert not source.exists()
    assert target.exists()

    # Now Rollback
    op_service.rollback_operation(op_id)

    # Assert
    assert source.exists()
    assert not target.exists()

    op_db = op_service.op_repo.get(op_id)
    assert op_db.rollback_available == 0
    assert op_db.rollback_at is not None

    rec_db = op_service.file_repo.get(file_id)
    assert rec_db.current_path == str(source)

def test_rollback_source_missing(op_service, tmp_workspace):
    tmpdir, archive_root = tmp_workspace
    source = tmpdir / "source.txt"
    target = archive_root / "target.txt"
    create_mock_file(source)

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="source.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)
    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])
    op_id = res["results"][0]["operation_id"]

    # Delete the target physically to simulate missing source during rollback
    target.unlink()

    with pytest.raises(RollbackError, match="Rollback source not found"):
        op_service.rollback_operation(op_id)

def test_rollback_target_already_exists(op_service, tmp_workspace):
    tmpdir, archive_root = tmp_workspace
    source = tmpdir / "source.txt"
    target = archive_root / "target.txt"
    create_mock_file(source)

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="source.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)
    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])
    op_id = res["results"][0]["operation_id"]

    # Re-create the source physically to simulate collision
    create_mock_file(source)

    with pytest.raises(RollbackError, match="Rollback target already exists"):
        op_service.rollback_operation(op_id)

@patch("app.repositories.operation_log_repository.OperationLogRepository.commit_successful_rollback")
def test_rollback_db_update_fails_rollback_file(mock_commit_db, op_service, tmp_workspace):
    mock_commit_db.side_effect = Exception("Simulated DB commit error")

    tmpdir, archive_root = tmp_workspace
    source = tmpdir / "source.txt"
    target = archive_root / "target.txt"
    create_mock_file(source)

    rec = FileRecord(original_path=str(source), current_path=str(source), filename="source.txt", size_bytes=4, status="active")
    file_id = op_service.file_repo.create(rec)
    sug = FileSuggestion(file_id=file_id, status="accepted", source_path=str(source), target_path=str(target), archive_root=str(archive_root), created_at=now_iso())
    with UnitOfWork():
        sug_id = op_service.sug_repo.create(sug)

    res = op_service.execute_suggestions([sug_id])
    op_id = res["results"][0]["operation_id"]

    with pytest.raises(RollbackError, match="Database update failed after rollback"):
        op_service.rollback_operation(op_id)

    # File must be reverted back to `target` because DB failed!
    assert not source.exists()
    assert target.exists()

def test_execute_partial_success(op_service, tmp_workspace):
    tmpdir, archive_root = tmp_workspace

    # 1. Success
    s1 = tmpdir / "s1.txt"
    t1 = archive_root / "t1.txt"
    create_mock_file(s1)
    rec1 = op_service.file_repo.create(FileRecord(original_path=str(s1), current_path=str(s1), filename="s1.txt", status="active", size_bytes=4))

    # 2. Failed (source missing)
    s2 = tmpdir / "s2.txt"
    t2 = archive_root / "t2.txt"
    rec2 = op_service.file_repo.create(FileRecord(original_path=str(s2), current_path=str(s2), filename="s2.txt", status="active", size_bytes=4))

    # 3. Success
    s3 = tmpdir / "s3.txt"
    t3 = archive_root / "t3.txt"
    create_mock_file(s3)
    rec3 = op_service.file_repo.create(FileRecord(original_path=str(s3), current_path=str(s3), filename="s3.txt", status="active", size_bytes=4))

    with UnitOfWork():
        sug1 = op_service.sug_repo.create(FileSuggestion(file_id=rec1, status="accepted", source_path=str(s1), target_path=str(t1), archive_root=str(archive_root), created_at=now_iso()))
        sug2 = op_service.sug_repo.create(FileSuggestion(file_id=rec2, status="accepted", source_path=str(s2), target_path=str(t2), archive_root=str(archive_root), created_at=now_iso()))
        sug3 = op_service.sug_repo.create(FileSuggestion(file_id=rec3, status="accepted", source_path=str(s3), target_path=str(t3), archive_root=str(archive_root), created_at=now_iso()))

    res = op_service.execute_suggestions([sug1, sug2, sug3])

    assert res["success_count"] == 2
    assert res["failed_count"] == 1

    assert not s1.exists()
    assert t1.exists()
    assert not s3.exists()
    assert t3.exists()

    sug_db1 = op_service.sug_repo.get(sug1)
    assert sug_db1.status == "executed"
    sug_db2 = op_service.sug_repo.get(sug2)
    assert sug_db2.status == "failed"
    sug_db3 = op_service.sug_repo.get(sug3)
    assert sug_db3.status == "executed"

    rec_db1 = op_service.file_repo.get(rec1)
    assert rec_db1.current_path == str(t1)
    rec_db2 = op_service.file_repo.get(rec2)
    assert rec_db2.current_path == str(s2)
    rec_db3 = op_service.file_repo.get(rec3)
    assert rec_db3.current_path == str(t3)

    ops, _ = op_service.op_repo.list_paginated()
    assert len(ops) == 3
    assert len([op for op in ops if op.status == "success"]) == 2
    assert len([op for op in ops if op.status == "failed"]) == 1
