import pytest
from app.services.ai_rule_draft_service import AIRuleDraftService
from app.models.ai_rule_draft import AIRuleDraft
from app.models.rule import Rule
from app.repositories.ai_rule_draft_repository import AIRuleDraftRepository
from app.core.database import get_connection, init_db
from fastapi import BackgroundTasks
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def setup_draft_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM ai_rule_drafts")
    conn.execute("DELETE FROM rules")
    conn.execute("INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES ('archive_root', 'D:/Archive', '2026-05-06T00:00:00')")
    conn.commit()

def test_generate_draft():
    svc = AIRuleDraftService()
    draft_id = svc.generate_draft("把毕业论文放进 University/Thesis")
    assert draft_id > 0

    draft = svc.draft_repo.get(draft_id)
    assert draft.status == "validated", f"Failed: {draft.validation_error}"
    assert draft.target_dir == "University/Thesis"
    assert draft.name == "AI生成的规则草案"

def test_generate_draft_invalid_path():
    svc = AIRuleDraftService()
    # Mock the LLM to return an invalid path
    original_generate = svc.llm_service.generate_rule_draft
    svc.llm_service.generate_rule_draft = lambda prompt, rules_context=None, directories_context=None: {
        "name": "Bad Rule",
        "target_dir": "C:/Windows/System32"
    }

    draft_id = svc.generate_draft("put files in system dir")
    draft = svc.draft_repo.get(draft_id)

    assert draft.status == "failed"
    assert "Invalid or unsafe target directory" in draft.validation_error

    # Restore mock
    svc.llm_service.generate_rule_draft = original_generate

def test_accept_draft():
    svc = AIRuleDraftService()
    draft_id = svc.generate_draft("把论文归档")

    bg_tasks = BackgroundTasks()
    rule = svc.accept_draft(draft_id, bg_tasks)
    assert rule is not None
    assert rule.name == "AI生成的规则草案"
    assert rule.target_dir == "University/Thesis"

    draft = svc.draft_repo.get(draft_id)
    assert draft.status == "converted"

def test_preview_draft():
    svc = AIRuleDraftService()
    draft_id = svc.generate_draft("把论文归档")

    preview = svc.get_preview(draft_id)
    assert preview["draft_id"] == draft_id
    assert "matched_count" in preview
    assert "items" in preview
