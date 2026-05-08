import pytest
from app.repositories.settings_repository import SettingsRepository
from app.core.database import get_connection

@pytest.fixture(autouse=True)
def setup_db():
    conn = get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)")
    conn.execute("DELETE FROM app_settings")
    conn.commit()

def test_settings_repository_get_and_set():
    repo = SettingsRepository()
    
    # Test get missing key
    assert repo.get("missing_key") is None
    
    # Test set key
    repo.set("my_key", "my_value")
    
    # Test get existing key
    assert repo.get("my_key") == "my_value"
    
    # Test update existing key
    repo.set("my_key", "new_value")
    assert repo.get("my_key") == "new_value"