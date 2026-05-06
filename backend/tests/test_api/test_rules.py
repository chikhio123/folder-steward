from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_connection, init_db
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM rules")
    conn.commit()

def test_create_and_list_rule():
    response = client.post("/api/rules", json={
        "name": "Test Rule",
        "rule_type": "extension",
        "pattern": ".abc",
        "target_dir": "TestDir"
    })
    assert response.status_code == 200
    rule_id = response.json()["id"]

    res2 = client.get("/api/rules")
    assert res2.status_code == 200
    items = res2.json()
    assert len(items) == 1
    assert items[0]["name"] == "Test Rule"

def test_update_and_delete_rule():
    response = client.post("/api/rules", json={
        "name": "Test Rule 2",
        "rule_type": "extension",
        "pattern": ".xyz",
        "target_dir": "TestDir"
    })
    rule_id = response.json()["id"]

    client.patch(f"/api/rules/{rule_id}", json={
        "name": "Updated Rule"
    })

    res = client.get("/api/rules")
    assert res.json()[0]["name"] == "Updated Rule"

    client.delete(f"/api/rules/{rule_id}")
    res = client.get("/api/rules")
    assert len(res.json()) == 0
