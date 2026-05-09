import pytest
from app.repositories.suggestion_repository import SuggestionRepository
from app.models.file_suggestion import FileSuggestion
from app.models.scan_task import now_iso
from app.core.uow import TransactionRequiredError, UnitOfWork
from app.core.database import get_connection, init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM file_suggestions")
    conn.execute("DELETE FROM ai_classification_suggestions")
    conn.execute("DELETE FROM file_records")
    conn.commit()

def test_repo_requires_transaction(setup_db):
    conn = get_connection()
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, size_bytes, indexed_at, status) VALUES (1, 'A', 'A', 'A', 1, '2026', 'active')")
    # Don't commit yet, wait we must commit because isolation_level=None but we are outside UoW
    # Actually setup_db might have done something. Just doing an insert.
    
    repo = SuggestionRepository()
    sug = FileSuggestion(
        file_id=1, suggestion_type="move", source_path="A", target_path="B",
        reason="", confidence=0.9, conflict_status="none", status="pending",
        archive_root="D:/", created_at=now_iso()
    )
    
    with pytest.raises(TransactionRequiredError):
        repo.create(sug)
        
    with pytest.raises(TransactionRequiredError):
        repo.update(sug)

    with pytest.raises(TransactionRequiredError):
        repo.update_status(1, "rejected")
        
    with pytest.raises(TransactionRequiredError):
        repo.bulk_update_status("pending", "rejected")

def test_repo_writes_within_uow(setup_db):
    conn = get_connection()
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, size_bytes, indexed_at, status) VALUES (1, 'A', 'A', 'A', 1, '2026', 'active')")

    repo = SuggestionRepository()
    sug = FileSuggestion(
        file_id=1, suggestion_type="move", source_path="A", target_path="B",
        reason="", confidence=0.9, conflict_status="none", status="pending",
        archive_root="D:/", created_at=now_iso()
    )
    
    with UnitOfWork():
        sug_id = repo.create(sug)
        
    assert sug_id is not None