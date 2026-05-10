import pytest
from app.services.rule_engine_service import RuleEngineService
from app.models.file_record import FileRecord
from app.models.file_content import FileContent
from app.models.rule import Rule
from app.repositories.rule_repository import RuleRepository
from app.core.database import get_connection, init_db
from app.core.uow import UnitOfWork
from pathlib import Path

@pytest.fixture
def setup_rules():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM rules")
    conn.commit()

    repo = RuleRepository()

    r1 = Rule(name="Ext Rule", rule_type="extension", pattern=".pdf,.docx", target_dir="Docs", priority=10)
    with UnitOfWork():
        repo.create(r1)

    r2 = Rule(name="FN Rule", rule_type="filename_keyword", pattern="invoice,receipt", target_dir="Finance", priority=20)
    with UnitOfWork():
        repo.create(r2)

    r3 = Rule(name="Content Rule", rule_type="content_keyword", pattern="philosophy,kant", target_dir="Books/Philosophy", priority=30)
    with UnitOfWork():
        repo.create(r3)

def test_rule_engine_extension(setup_rules):
    svc = RuleEngineService()
    f = FileRecord(
        original_path="a.pdf",
        current_path="a.pdf",
        filename="a.pdf",
        extension=".pdf",
        size_bytes=100,
        indexed_at="2026-05-06T00:00:00"
    )
    match = svc.match(f, None)
    assert match is not None
    assert match.rule.name == "Ext Rule"

    target = svc.build_target_path(f, match, Path("Archive"))
    assert str(target).endswith(str(Path("Docs/a.pdf")))

def test_rule_engine_filename_keyword(setup_rules):
    svc = RuleEngineService()
    f = FileRecord(
        original_path="invoice_2026.pdf",
        current_path="invoice_2026.pdf",
        filename="invoice_2026.pdf",
        extension=".pdf",
        size_bytes=100,
        indexed_at="2026-05-06T00:00:00"
    )
    # Should match FN Rule due to higher priority than Ext Rule
    match = svc.match(f, None)
    assert match is not None
    assert match.rule.name == "FN Rule"

def test_rule_engine_content_keyword(setup_rules):
    svc = RuleEngineService()
    f = FileRecord(
        original_path="random.txt",
        current_path="random.txt",
        filename="random.txt",
        extension=".txt",
        size_bytes=100,
        indexed_at="2026-05-06T00:00:00"
    )
    c = FileContent(
        file_id=1,
        text_content="This text talks about Kant and his theories.",
        text_length=50,
        extractor_type="TxtExtractor",
        extract_status="completed"
    )
    match = svc.match(f, c)
    assert match is not None
    assert match.rule.name == "Content Rule"
