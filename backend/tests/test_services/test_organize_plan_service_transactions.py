import pytest
from unittest.mock import MagicMock
from app.services.organize_plan_service import OrganizePlanService
from app.models.organize_plan import OrganizePlan
from app.models.organize_plan_item import OrganizePlanItem
from app.core.database import get_connection, init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    tables = [
        "file_suggestions", "file_contents", "extract_tasks",
        "operation_logs", "semantic_group_items", "file_tags",
        "ai_classification_suggestions", "organize_plan_items",
        "file_summaries", "file_records", "organize_plans"
    ]
    for t in tables:
        conn.execute(f"DELETE FROM {t}")
    conn.commit()
    yield
    from app.main import app
    app.dependency_overrides.clear()

def test_accept_plan_transaction_state():
    conn = get_connection()
    
    # Setup File Record
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, size_bytes, indexed_at, status) VALUES (10, 'A.txt', 'A.txt', 'A.txt', 100, '2026-05-08', 'active')")
    
    # Setup AI Classification Suggestion
    conn.execute("INSERT INTO ai_classification_suggestions (id, file_id, suggested_target_dir, confidence, status, created_at) VALUES (100, 10, 'Docs', 0.9, 'pending', '2026-05-08')")
    
    # Setup Plan
    conn.execute("INSERT INTO organize_plans (id, title, scope, status, created_at) VALUES (1, 'Test', 'all', 'draft', '2026-05-08')")
    
    # Setup Plan Item
    conn.execute("INSERT INTO organize_plan_items (id, plan_id, file_id, ai_suggestion_id, source_path, target_dir, target_path, directory_status, confidence, status, created_at) VALUES (55, 1, 10, 100, 'A.txt', 'Docs', 'D:/Docs/A.txt', 'existing', 0.9, 'pending', '2026-05-08')")
    
    conn.commit()
    
    # Mock settings repo for archive root
    mock_settings = MagicMock()
    mock_settings.get.return_value = "D:/Archive"
    
    # Use real repositories
    from app.repositories.organize_plan_repository import OrganizePlanRepository
    from app.repositories.suggestion_repository import SuggestionRepository
    from app.repositories.ai_classification_repository import AIClassificationRepository
    
    svc = OrganizePlanService(
        plan_repo=OrganizePlanRepository(),
        class_repo=AIClassificationRepository(),
        suggestion_repo=SuggestionRepository(),
        settings_repo=mock_settings,
        classification_service=MagicMock(),
    )

    # Act
    svc.accept_plan(1)

    # Assert
    # 1. file_suggestions inserted
    sugs = conn.execute("SELECT * FROM file_suggestions").fetchall()
    assert len(sugs) == 1
    assert sugs[0]["file_id"] == 10

    # 2. organize_plan_items.status = converted
    items = conn.execute("SELECT status FROM organize_plan_items WHERE id=55").fetchall()
    assert items[0]["status"] == "converted"

    # 3. ai_classification_suggestions.status = converted
    ai_sugs = conn.execute("SELECT status FROM ai_classification_suggestions WHERE id=100").fetchall()
    assert ai_sugs[0]["status"] == "converted"

    # 4. organize_plans.status = converted
    plans = conn.execute("SELECT status, updated_at FROM organize_plans WHERE id=1").fetchall()
    assert plans[0]["status"] == "converted"
    assert plans[0]["updated_at"] is not None

def test_reject_plan_transaction_state():
    conn = get_connection()

    # Setup File Record
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, size_bytes, indexed_at, status) VALUES (10, 'A.txt', 'A.txt', 'A.txt', 100, '2026-05-08', 'active')")

    # Setup AI Classification Suggestion (converted)
    conn.execute("INSERT INTO ai_classification_suggestions (id, file_id, suggested_target_dir, confidence, status, created_at) VALUES (100, 10, 'Docs', 0.9, 'converted', '2026-05-08')")

    # Setup Plan
    conn.execute("INSERT INTO organize_plans (id, title, scope, status, created_at) VALUES (1, 'Test', 'all', 'draft', '2026-05-08')")

    # Setup Plan Item
    conn.execute("INSERT INTO organize_plan_items (id, plan_id, file_id, ai_suggestion_id, source_path, target_dir, target_path, directory_status, confidence, status, created_at) VALUES (55, 1, 10, 100, 'A.txt', 'Docs', 'D:/Docs/A.txt', 'existing', 0.9, 'converted', '2026-05-08')")

    conn.commit()

    from app.repositories.organize_plan_repository import OrganizePlanRepository
    from app.repositories.ai_classification_repository import AIClassificationRepository

    svc = OrganizePlanService(
        plan_repo=OrganizePlanRepository(),
        class_repo=AIClassificationRepository(),
        classification_service=MagicMock(),
    )
    
    # Act
    svc.reject_plan(1)
    
    # Assert
    # 1. organize_plan_items.status = rejected
    items = conn.execute("SELECT status FROM organize_plan_items WHERE id=55").fetchall()
    assert items[0]["status"] == "rejected"
    
    # 2. ai_classification_suggestions.status = pending (restored)
    ai_sugs = conn.execute("SELECT status FROM ai_classification_suggestions WHERE id=100").fetchall()
    assert ai_sugs[0]["status"] == "pending"
    
    # 3. organize_plans.status = rejected
    plans = conn.execute("SELECT status, updated_at FROM organize_plans WHERE id=1").fetchall()
    assert plans[0]["status"] == "rejected"
    assert plans[0]["updated_at"] is not None