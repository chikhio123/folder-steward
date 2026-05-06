from fastapi import APIRouter, Query
from typing import Optional

from ..schemas.search_schema import SearchResponse, SearchResultItem
from ..services.search_service import SearchService

router = APIRouter(tags=["search"])
search_service = SearchService()

@router.get("/search", response_model=SearchResponse)
def search_files(
    q: str = Query(..., min_length=1),
    scope: str = Query("all"),
    extension: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    items, total = search_service.search(
        query=q,
        scope=scope,
        extension=extension,
        page=page,
        page_size=page_size,
    )

    return SearchResponse(
        items=[SearchResultItem(**item) for item in items],
        total=total
    )

@router.post("/search/rebuild-index")
def rebuild_index():
    from ..services.extract_service import ExtractService
    svc = ExtractService()

    # Rebuild all (missing, failed, stale) in a single optimized pass
    created, _ = svc.create_extract_tasks(mode="rebuild_all")

    return {"queued_tasks": created}
