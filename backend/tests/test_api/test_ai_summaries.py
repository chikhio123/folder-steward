from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_connection, init_db
from app.models.file_record import FileRecord
from app.repositories.file_repository import FileRepository
import pytest
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM file_summaries")
    conn.execute("DELETE FROM ai_tasks")
    conn.execute("DELETE FROM file_records")
    conn.commit()

@patch("app.api.ai_summaries.queue_service")
def test_create_summary_task(mock_queue):
    mock_queue.enqueue_task.return_value = 99

    # Create a file record
    repo = FileRepository()
    file_id = repo.create(FileRecord(
        original_path="test.txt", current_path="test.txt", filename="test.txt",
        size_bytes=100, indexed_at="2026-05-06T00:00:00"
    ))

    # Request summary
    res = client.post("/api/ai/summaries", json={"file_id": file_id})
    assert res.status_code == 200
    assert res.json() == {"task_id": 99, "status": "pending"}

    # Verify that a pending placeholder was created in the database
    conn = get_connection()
    summary = conn.execute("SELECT status FROM file_summaries WHERE file_id=?", (file_id,)).fetchone()
    assert summary is not None
    assert summary["status"] == "pending"

def test_get_file_summary_not_found():
    res = client.get("/api/files/999/summary")
    assert res.status_code == 404
