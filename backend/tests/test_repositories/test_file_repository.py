import pytest
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

def test_repo_active_excluding_prefix(setup_db):
    from app.repositories.file_repository import FileRepository
    repo = FileRepository()
    
    res = repo.get_active_excluding_prefix("D:/Archive")
    assert isinstance(res, list)
    res_all = repo.get_all_active_ids()
    assert isinstance(res_all, list)