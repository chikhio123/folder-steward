import pytest
from app.core.database import get_connection, init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM file_records")
    conn.commit()

def test_repo_active_excluding_prefix(setup_db):
    from app.repositories.file_repository import FileRepository
    repo = FileRepository()
    
    res = repo.get_active_excluding_prefix("D:/Archive")
    assert isinstance(res, list)
    res_all = repo.get_all_active_ids()
    assert isinstance(res_all, list)