import pytest
from unittest.mock import MagicMock
from app.services.organize_plan_service import OrganizePlanService


def test_generate_plan_requires_classification_service():
    with pytest.raises(ValueError, match="classification_service is required"):
        OrganizePlanService()


def test_generate_plan_no_archive_root_raises():
    mock_settings = MagicMock()
    mock_settings.get.return_value = None

    mock_class_svc = MagicMock()

    svc = OrganizePlanService(
        classification_service=mock_class_svc,
        settings_repo=mock_settings,
    )

    with pytest.raises(ValueError, match="archive_root is not configured"):
        svc.generate_plan(scope="all")

    mock_class_svc.process_classification_batch.assert_not_called()


def test_generate_plan_happy_path():
    """Verify the full generate_plan flow with real DB + mocked repos."""
    from app.core.database import get_connection, init_db
    init_db()
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys=OFF")
    for t in ("file_suggestions", "file_contents", "extract_tasks",
              "operation_logs", "semantic_group_items", "file_tags",
              "ai_classification_suggestions", "organize_plan_items",
              "organize_plans", "file_summaries", "file_records"):
        conn.execute(f"DELETE FROM {t}")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES ('archive_root', 'D:/Archive', '2026-01-01')")
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, extension, size_bytes, indexed_at, status) VALUES (1, 'doc.txt', 'doc.txt', 'doc.txt', '.txt', 100, '2026-01-01', 'active')")
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, extension, size_bytes, indexed_at, status) VALUES (2, 'sheet.csv', 'sheet.csv', 'sheet.csv', '.csv', 200, '2026-01-01', 'active')")
    conn.commit()

    mock_plan_repo = MagicMock()
    mock_plan_repo.create_plan.return_value = 42
    mock_class_repo = MagicMock()
    mock_class_repo.get_pending_with_paths.return_value = [
        {"file_id": 1, "suggestion_id": 101, "current_path": "doc.txt",
         "suggested_target_dir": "Documents", "directory_status": "existing",
         "confidence": 0.9, "reason": "It's a doc", "evidence_json": None},
        {"file_id": 2, "suggestion_id": 102, "current_path": "sheet.csv",
         "suggested_target_dir": "Documents", "directory_status": "existing",
         "confidence": 0.85, "reason": "It's a sheet", "evidence_json": None},
    ]
    mock_class_repo.delete_pending_by_files.return_value = None
    mock_class_svc = MagicMock()
    mock_path_prot = MagicMock()
    mock_path_prot.filter_file_ids.return_value = ([1, 2], 0)

    from app.repositories.settings_repository import SettingsRepository
    from app.repositories.file_repository import FileRepository

    svc = OrganizePlanService(
        plan_repo=mock_plan_repo,
        class_repo=mock_class_repo,
        path_protection=mock_path_prot,
        classification_service=mock_class_svc,
        settings_repo=SettingsRepository(),
        file_repo=FileRepository(),
    )

    plan_id = svc.generate_plan(scope="all")

    assert plan_id == 42
    mock_class_svc.process_classification_batch.assert_called_once_with(
        [1, 2], "D:/Archive", batch_size=20, task=None
    )
    mock_class_repo.delete_pending_by_files.assert_called_once_with([1, 2])
    mock_plan_repo.create_plan.assert_called_once()
    mock_class_repo.update_status_batch.assert_called_once_with(
        [101, 102], "in_plan"
    )
    mock_plan_repo.update_plan.assert_called_once()