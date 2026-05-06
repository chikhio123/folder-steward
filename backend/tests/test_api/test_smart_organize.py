from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_connection, init_db
from app.models.organize_plan import OrganizePlan
from app.models.organize_plan_item import OrganizePlanItem
from app.repositories.organize_plan_repository import OrganizePlanRepository
import pytest
from unittest.mock import patch

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM organize_plans")
    conn.execute("DELETE FROM organize_plan_items")
    conn.execute("DELETE FROM ai_tasks")
    conn.commit()

@patch("app.api.smart_organize.queue_service")
def test_create_classification_tasks(mock_queue):
    mock_queue.enqueue_task.return_value = 1

    res = client.post("/api/ai/classify", json={"file_ids": [10, 20], "archive_root": "D:/Archive"})
    assert res.status_code == 200
    assert res.json()["task_id"] == 1
    assert res.json()["queued_count"] == 2

@patch("app.api.smart_organize.queue_service")
def test_create_organize_plan(mock_queue):
    mock_queue.enqueue_task.return_value = 2

    res = client.post("/api/ai/organize-plans", json={"scope": "others", "archive_root": "D:/Archive", "min_confidence": 0.8})
    assert res.status_code == 200
    assert res.json()["task_id"] == 2

def test_get_plan_preview():
    # Insert a dummy plan and file record
    conn = get_connection()
    cur = conn.execute("INSERT INTO file_records (original_path, current_path, filename, size_bytes, indexed_at, status) VALUES (?, ?, ?, ?, ?, ?)",
                 ("C:/a.txt", "C:/a.txt", "a.txt", 100, "2026-05-06T00:00:00", "active"))
    file_id = cur.lastrowid
    conn.commit()

    repo = OrganizePlanRepository()
    plan_id = repo.create_plan(OrganizePlan(title="Test Plan", scope="all", status="draft"))
    repo.create_item(OrganizePlanItem(
        plan_id=plan_id, file_id=file_id, source_path="C:/a.txt", target_dir="Docs",
        target_path="D:/Archive/Docs/a.txt", status="pending"
    ))

    res = client.get(f"/api/ai/organize-plans/{plan_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test Plan"
    assert "Docs" in data["groups"]
    assert len(data["groups"]["Docs"]) == 1

@patch("app.api.smart_organize.plan_service")
def test_accept_organize_plan(mock_plan_service):
    res = client.post("/api/ai/organize-plans/1/accept")
    assert res.status_code == 200
    mock_plan_service.accept_plan.assert_called_once_with(1)

@patch("app.api.smart_organize.plan_service")
def test_reject_organize_plan(mock_plan_service):
    res = client.post("/api/ai/organize-plans/1/reject")
    assert res.status_code == 200
    mock_plan_service.reject_plan.assert_called_once_with(1)
