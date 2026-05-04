from fastapi import APIRouter
from typing import Optional

from ..core.config import settings
from ..core.database import get_connection

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


@router.put("/settings")
def update_settings(body: dict[str, str]):
    conn = get_connection()
    from ..models.scan_task import now_iso
    now = now_iso()
    for key, value in body.items():
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now),
        )
    conn.commit()
    rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}
