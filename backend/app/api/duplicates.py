from fastapi import APIRouter
from pydantic import BaseModel

from ..repositories.file_repository import FileRepository
from ..services.duplicate_service import DuplicateService

router = APIRouter(tags=["duplicates"])
file_repo = FileRepository()


@router.get("/duplicates")
def list_duplicates():
    groups = file_repo.find_duplicate_groups()
    return {"groups": groups}


class GenerateDuplicateSuggestionsRequest(BaseModel):
    sha256: str
    filename: str
    keep_file_id: int

@router.post("/duplicates/suggestions")
def create_duplicate_suggestions(body: GenerateDuplicateSuggestionsRequest):
    svc = DuplicateService()
    created = svc.create_duplicate_suggestions(body.sha256, body.filename, body.keep_file_id)
    return {"created_count": created}
