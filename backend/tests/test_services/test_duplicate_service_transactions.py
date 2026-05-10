import pytest
from unittest.mock import MagicMock
from app.services.duplicate_service import DuplicateService
from app.core.database import get_connection, init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    tables = [

        "file_suggestions", "file_contents", "extract_tasks",

        "operation_logs", "semantic_group_items", "file_tags",

        "ai_classification_suggestions", "organize_plan_items",

        "file_summaries", "file_records", "organize_plans", "app_settings"

    ]

    for t in tables:

        conn.execute(f"DELETE FROM {t}")
    conn.commit()
    yield
    from app.main import app
    app.dependency_overrides.clear()

def test_isolate_duplicates_uses_uow(monkeypatch):
    conn = get_connection()
    
    # Insert mock file records
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, size_bytes, indexed_at, sha256, status) VALUES (1, 'A.txt', 'A.txt', 'A.txt', 100, '2026-05-08', 'hash123', 'active')")
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, size_bytes, indexed_at, sha256, status) VALUES (2, 'B.txt', 'B.txt', 'A.txt', 100, '2026-05-08', 'hash123', 'active')")
    
    # Insert archive root setting
    conn.execute("INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES ('archive_root', 'D:/Archive', '2026')")
    conn.commit()

    svc = DuplicateService()
    
    # We only test the isolate_duplicates function locally without calling OperationService.execute_suggestions
    # So we monkeypatch it out
    from app.services.operation_service import OperationService
    mock_execute = MagicMock(return_value={"success_count": 1, "failed_count": 0, "results": [], "skipped": []})
    monkeypatch.setattr(OperationService, "execute_suggestions", mock_execute)
    
    groups = [{
        "sha256": "hash123",
        "keep_file_id": 1
    }]
    
    # Call isolate_duplicates, should not raise TransactionRequiredError
    res = svc.isolate_duplicates(groups)
    
    # Verify the operation service was called
    mock_execute.assert_called_once()
    
    # Verify the DB state: suggestion was created inside a UoW
    sugs = conn.execute("SELECT * FROM file_suggestions WHERE suggestion_type='move_duplicate'").fetchall()
    assert len(sugs) == 1
    assert sugs[0]["file_id"] == 2