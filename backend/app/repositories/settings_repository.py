from ..core.database import get_connection, require_transaction
from ..models.scan_task import now_iso

class SettingsRepository:
    def get(self, key: str) -> str | None:
        conn = get_connection()
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        require_transaction()
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now_iso())
        )

    def get_all(self) -> dict[str, str]:
        conn = get_connection()
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def update_all(self, settings: dict[str, str]) -> None:
        require_transaction()
        conn = get_connection()
        for k, v in settings.items():
            conn.execute(
                "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
                (k, v, now_iso()),
            )