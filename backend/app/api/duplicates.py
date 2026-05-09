from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from ..repositories.file_repository import FileRepository
from ..services.duplicate_service import DuplicateService

router = APIRouter(tags=["duplicates"])
file_repo = FileRepository()


@router.get("/duplicates")
def list_duplicates():
    groups = file_repo.find_duplicate_groups()
    return {"groups": groups}


class DuplicateGroupItem(BaseModel):
    sha256: str
    filename: Optional[str] = None
    keep_file_id: Optional[int] = None

class IsolateDuplicatesRequest(BaseModel):
    mode: str  # "auto" or "manual"
    groups: Optional[List[DuplicateGroupItem]] = None

@router.post("/duplicates/isolation-plan")
def isolate_duplicates(body: IsolateDuplicatesRequest):
    svc = DuplicateService()
    groups_to_process = []

    if body.mode == "auto":
        # Process all duplicate groups
        db_groups = svc.find_groups()
        for g in db_groups:
            groups_to_process.append({"sha256": g["sha256"], "filename": g["filename"]})
    else:
        if not body.groups:
            return {"success_count": 0, "failed_count": 0, "results": [], "skipped": []}
        groups_to_process = [g.dict() for g in body.groups]

    result = svc.isolate_duplicates(groups_to_process, auto_mode=(body.mode == "auto"))
    return result
