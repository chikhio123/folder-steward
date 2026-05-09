from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Dict
import httpx

from ..core.config import settings
from ..dependencies import get_settings_repository
from ..repositories.settings_repository import SettingsRepository

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=Dict[str, str])
def get_settings(settings_repo: SettingsRepository = Depends(get_settings_repository)):
    return settings_repo.get_all()


@router.put("/settings", response_model=Dict[str, str])
def update_settings(body: dict[str, str], settings_repo: SettingsRepository = Depends(get_settings_repository)):
    settings_repo.update_all(body)
    return settings_repo.get_all()


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
