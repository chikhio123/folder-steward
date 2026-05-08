from app.core.database import get_connection
from app.models.scan_task import now_iso

class SettingsRepository:
    def get(self, key: str) -> str | None:
        conn = get_connection()
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now_iso())
        )
        conn.commit()