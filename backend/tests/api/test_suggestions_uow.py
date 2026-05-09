import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_connection, init_db
from app.dependencies import get_suggestion_repository

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM file_suggestions")
    conn.execute("DELETE FROM ai_classification_suggestions")
    conn.execute("DELETE FROM file_records")
    conn.commit()

def test_bulk_reject_rolls_back_on_error(setup_db):
    conn = get_connection()
    conn.execute("INSERT INTO file_records (id, original_path, current_path, filename, size_bytes, indexed_at, status) VALUES (1, 'A', 'A', 'A', 1, '2026', 'active')")
    conn.execute("INSERT INTO file_suggestions (file_id, status, suggestion_type, source_path, target_path, created_at) VALUES (1, 'pending', 'move', 'A', 'B', '2026')")
    conn.commit()

    from app.repositories.suggestion_repository import SuggestionRepository
    class FailingSuggestionRepo(SuggestionRepository):
        def bulk_update_status(self, current_status, new_status):
            super().bulk_update_status(current_status, new_status)
            raise ValueError("Simulated crash")
            
    app.dependency_overrides[get_suggestion_repository] = lambda: FailingSuggestionRepo()
    
    try:
        response = client.post("/api/suggestions/bulk-reject", json={"status": "pending"})
        assert response.status_code == 500
        
        # Assert DB rolled back and record is still pending
        row = conn.execute("SELECT status FROM file_suggestions WHERE file_id=1").fetchone()
        assert row["status"] == "pending"
    finally:
        app.dependency_overrides.clear()