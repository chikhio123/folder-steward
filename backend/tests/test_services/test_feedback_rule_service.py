import pytest
from app.services.feedback_rule_service import FeedbackRuleService
from app.core.database import get_connection, init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM operation_logs")
    conn.commit()

def test_analyze_recent_operations_no_pattern():
    svc = FeedbackRuleService()
    patterns = svc.analyze_recent_operations()
    assert len(patterns) == 0

def test_analyze_recent_operations_matches_pattern():
    conn = get_connection()
    # Insert 3 successful moves to the same directory
    for i in range(3):
        conn.execute(
            """INSERT INTO operation_logs (operation_type, source_path, target_path, status, executed_at)
               VALUES ('move', ?, ?, 'success', '2026-05-06T00:00:00')""",
            (f"C:/source{i}.txt", f"D:/Archive/TargetDir/file{i}.txt")
        )
    # Insert 1 successful move to another dir
    conn.execute(
        """INSERT INTO operation_logs (operation_type, source_path, target_path, status, executed_at)
           VALUES ('move', 'C:/other.txt', 'D:/Archive/OtherDir/other.txt', 'success', '2026-05-06T00:00:00')"""
    )
    conn.commit()

    svc = FeedbackRuleService()
    patterns = svc.analyze_recent_operations()

    assert len(patterns) == 1
    assert patterns[0]["target_dir"] == "D:/Archive/TargetDir"
    assert patterns[0]["move_count"] == 3
    assert "建议创建一个自动化规则" in patterns[0]["suggestion_prompt"]
