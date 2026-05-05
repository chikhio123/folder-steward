from fastapi import APIRouter, HTTPException
from typing import Optional

from ..schemas.file_content_schema import FileContentResponse
from ..repositories.file_content_repository import FileContentRepository

router = APIRouter(tags=["file-contents"])
content_repo = FileContentRepository()

@router.get("/files/{file_id}/content", response_model=FileContentResponse)
def get_file_content(file_id: int):
    content = content_repo.get_by_file_id(file_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    preview = None
    if content.text_content:
        preview = content.text_content[:5000]

    return FileContentResponse(
        file_id=content.file_id,
        extract_status=content.extract_status,
        text_length=content.text_length,
        preview=preview,
        extracted_at=content.extracted_at,
    )
