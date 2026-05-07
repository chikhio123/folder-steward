from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import httpx

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


@router.get("/settings/models")
async def fetch_models(base_url: str = Query(...), api_key: str = Query(...)):
    """Fetch available models from an OpenAI-compatible /v1/models endpoint."""
    if not base_url:
        raise HTTPException(status_code=400, detail="Base URL is required")

    # Ensure it ends with /models if it's an OpenAI compatible endpoint
    # Usually base_url is like https://api.openai.com/v1
    endpoint = base_url.rstrip("/")
    if not endpoint.endswith("/models"):
        if not endpoint.endswith("/v1"):
            endpoint = f"{endpoint}/v1/models"
        else:
            endpoint = f"{endpoint}/models"

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            if "data" in data:
                models = [m.get("id") for m in data["data"] if "id" in m]
                # Sort alphabetically
                models.sort()
                return {"models": models}
            else:
                return {"models": []}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch models: {str(e)}")
