import sqlite3

def run_lightweight_migrations(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(file_suggestions)").fetchall()
    }
    if "archive_root" not in columns:
        conn.execute("ALTER TABLE file_suggestions ADD COLUMN archive_root TEXT")

    ai_tasks_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(ai_tasks)").fetchall()
    }
    if "retry_count" not in ai_tasks_cols and len(ai_tasks_cols) > 0:
        conn.execute("ALTER TABLE ai_tasks ADD COLUMN retry_count INTEGER DEFAULT 0")

    # Migrations for organize_plan_items: add ai_suggestion_id
    plan_item_cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(organize_plan_items)").fetchall()
    }
    if "ai_suggestion_id" not in plan_item_cols and len(plan_item_cols) > 0:
        conn.execute("ALTER TABLE organize_plan_items ADD COLUMN ai_suggestion_id INTEGER")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_items_suggestion ON organize_plan_items(ai_suggestion_id)")
