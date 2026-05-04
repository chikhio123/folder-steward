from fastapi import APIRouter

from ..repositories.file_repository import FileRepository

router = APIRouter(tags=["duplicates"])
file_repo = FileRepository()


@router.get("/duplicates")
def list_duplicates():
    groups = file_repo.find_duplicate_groups()
    return {"groups": groups}
