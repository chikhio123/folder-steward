import pytest
from app.core.database import get_connection, init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM ai_classification_suggestions")
    conn.commit()

def test_repo_custom_methods(setup_db):
    from app.repositories.ai_classification_repository import AIClassificationRepository
    repo = AIClassificationRepository()
    
    # We just need to verify the methods exist and execute without syntax errors
    from app.core.uow import UnitOfWork
    with UnitOfWork():
        repo.delete_pending_by_files([1, 2, 3])
        repo.update_status_batch([1, 2], "in_plan")
    res = repo.get_pending_with_paths([1, 2], 0.5)
    assert isinstance(res, list)