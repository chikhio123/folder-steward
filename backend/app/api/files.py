from fastapi import APIRouter, Query
from typing import Optional

from ..repositories.file_repository import FileRepository
from ..schemas.file_schema import FileRecordResponse, FileListResponse

router = APIRouter(tags=["files"])
file_repo = FileRepository()


@router.get("/files", response_model=FileListResponse)
def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    extension: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    duplicated: Optional[bool] = Query(None),
    sort_by: str = Query("modified_at"),
    sort_order: str = Query("desc"),
):
    records, total = file_repo.list_paginated(
        page=page,
        page_size=page_size,
        extension=extension,
        keyword=keyword,
        duplicated=duplicated,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return FileListResponse(
        items=[
            FileRecordResponse(
                id=r.id,
                filename=r.filename,
                original_path=r.original_path,
                current_path=r.current_path,
                extension=r.extension,
                size_bytes=r.size_bytes,
                sha256=r.sha256,
                modified_at=r.modified_at,
                status=r.status,
            )
            for r in records
        ],
        total=total,
    )
