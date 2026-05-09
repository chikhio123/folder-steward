import pytest
from backend.app.models.file_record import FileRecord
from backend.app.models.file_suggestion import FileSuggestion
from backend.app.models.scan_task import now_iso
from backend.app.repositories.file_repository import FileRepository
from backend.app.repositories.suggestion_repository import SuggestionRepository

@pytest.fixture
def repo():
    return SuggestionRepository()

@pytest.fixture
def file_repo():
    return FileRepository()

@pytest.fixture
def file_id(file_repo):
    rec = FileRecord(
        original_path="/test",
        current_path="/test",
        filename="test.txt",
        size_bytes=100,
        indexed_at=now_iso(),
    )
    return file_repo.create(rec)

def test_mark_superseded_routine(repo, file_id):
    # Routine task without include_accepted
    # 1. Create a pending, accepted, and failed suggestion
    s1 = FileSuggestion(file_id=file_id, status="pending", target_path="/t1", created_at=now_iso())
    s2 = FileSuggestion(file_id=file_id, status="accepted", target_path="/t2", created_at=now_iso())
    s3 = FileSuggestion(file_id=file_id, status="failed", target_path="/t3", created_at=now_iso())

    id1 = repo.create(s1)
    id2 = repo.create(s2)
    id3 = repo.create(s3)

    # 2. Call without include_accepted
    repo.mark_superseded_for_file(file_id)

    # 3. Assert pending and failed are superseded, accepted is unchanged
    assert repo.get(id1).status == "superseded"
    assert repo.get(id2).status == "accepted"
    assert repo.get(id3).status == "superseded"

def test_mark_superseded_duplicate_isolation(repo, file_id):
    # Duplicate isolation WITH include_accepted
    # 1. Create a pending, accepted, and failed suggestion
    s1 = FileSuggestion(file_id=file_id, status="pending", target_path="/t1", created_at=now_iso())
    s2 = FileSuggestion(file_id=file_id, status="accepted", target_path="/t2", created_at=now_iso())
    s3 = FileSuggestion(file_id=file_id, status="failed", target_path="/t3", created_at=now_iso())

    id1 = repo.create(s1)
    id2 = repo.create(s2)
    id3 = repo.create(s3)

    # 2. Call with include_accepted=True
    repo.mark_superseded_for_file(file_id, include_accepted=True)

    # 3. Assert all are superseded
    assert repo.get(id1).status == "superseded"
    assert repo.get(id2).status == "superseded"
    assert repo.get(id3).status == "superseded"
