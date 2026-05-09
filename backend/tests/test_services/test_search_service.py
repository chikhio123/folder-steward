import pytest
from app.services.search_service import SearchService
from app.models.file_record import FileRecord
from app.models.file_content import FileContent
from app.repositories.file_repository import FileRepository
from app.repositories.file_content_repository import FileContentRepository
from app.core.database import get_connection, init_db

@pytest.fixture
def setup_fts_data():
    init_db()
    conn = get_connection()
    # Clean up
    conn.execute("DELETE FROM file_contents")
    conn.execute("DELETE FROM extract_tasks")
    conn.execute("DELETE FROM file_suggestions")
    conn.execute("DELETE FROM ai_classification_suggestions")
    conn.execute("DELETE FROM file_records")
    conn.execute("DELETE FROM file_content_fts")
    conn.commit()

    repo = FileRepository()
    crepo = FileContentRepository()

    # Record 1
    r1 = FileRecord(
        original_path="a/test_document.txt",
        current_path="a/test_document.txt",
        filename="test_document.txt",
        extension=".txt",
        size_bytes=100,
        indexed_at="2026-05-06T00:00:00",
        status="active"
    )
    id1 = repo.create(r1)

    c1 = FileContent(
        file_id=id1,
        text_content="This is a dummy document containing specific search keywords like Kant and philosophy.",
        text_length=80,
        extractor_type="TxtExtractor",
        extract_status="completed"
    )
    crepo.create(c1)

    # Record 2
    r2 = FileRecord(
        original_path="b/another_file.pdf",
        current_path="b/another_file.pdf",
        filename="Kant_summary.pdf",
        extension=".pdf",
        size_bytes=200,
        indexed_at="2026-05-06T00:00:00",
        status="active"
    )
    id2 = repo.create(r2)

    c2 = FileContent(
        file_id=id2,
        text_content="A completely different file.",
        text_length=30,
        extractor_type="PdfExtractor",
        extract_status="completed"
    )
    crepo.create(c2)

    return id1, id2

def test_search_all_scope(setup_fts_data):
    id1, id2 = setup_fts_data
    svc = SearchService()

    # Match content in id1
    items, total = svc.search("philosophy", scope="all")
    assert total == 1
    assert items[0]["file_id"] == id1
    assert items[0]["match_source"] == "content"
    assert "<mark>" in items[0]["snippet"]

    # Match filename in id2
    items, total = svc.search("Kant", scope="all")
    # Note: because of the insert triggers, Kant is in id1 content and id2 filename
    # Actually, trigram splits 'Kant' and we might get unexpected matches.
    # We just need to assert both files are found and sources differ.
    assert total >= 2
    sources = [i["match_source"] for i in items]
    assert "filename" in sources
    assert "content" in sources

def test_search_filename_scope(setup_fts_data):
    id1, id2 = setup_fts_data
    svc = SearchService()

    items, total = svc.search("Kant", scope="filename")
    assert total >= 1
    # Check that at least id2 is found
    file_ids = [i["file_id"] for i in items]
    assert id2 in file_ids
    assert items[0]["match_source"] == "filename"

def test_search_content_scope(setup_fts_data):
    id1, id2 = setup_fts_data
    svc = SearchService()

    items, total = svc.search("Kant", scope="content")
    assert total == 1
    assert items[0]["file_id"] == id1
    assert items[0]["match_source"] == "content"

def test_search_with_extension_filter(setup_fts_data):
    id1, id2 = setup_fts_data
    svc = SearchService()

    # 'Kant' matches both, but filter by .txt
    items, total = svc.search("Kant", scope="all", extension=".txt")
    assert total == 1
    assert items[0]["file_id"] == id1
