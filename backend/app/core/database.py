import sqlite3
import threading
from pathlib import Path

from .config import settings

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    conn = getattr(_local, "connection", None)
    db_path = str(Path(settings.database_path))

    # If the connection exists but points to a different DB (e.g. in tests), close it
    if conn is not None:
        if getattr(_local, "db_path", None) != db_path:
            conn.close()
            conn = None

    if conn is None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # Use isolation_level=None for autocommit mode so read transactions don't stay open
        conn = sqlite3.connect(db_path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.connection = conn
        _local.db_path = db_path
    return conn


def close_connection() -> None:
    conn = getattr(_local, "connection", None)
    if conn:
        conn.close()
        _local.connection = None


def init_db() -> None:
    """Create all tables if they don't exist."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS file_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT NOT NULL,
            current_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            extension TEXT,
            mime_type TEXT,
            size_bytes INTEGER NOT NULL,
            sha256 TEXT,
            created_at TEXT,
            modified_at TEXT,
            indexed_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            last_error TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_file_records_current_path ON file_records(current_path);
        CREATE INDEX IF NOT EXISTS idx_file_records_extension ON file_records(extension);
        CREATE INDEX IF NOT EXISTS idx_file_records_sha256 ON file_records(sha256);
        CREATE INDEX IF NOT EXISTS idx_file_records_size_sha ON file_records(size_bytes, sha256);
        CREATE INDEX IF NOT EXISTS idx_file_records_status ON file_records(status);

        CREATE TABLE IF NOT EXISTS scan_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            root_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            total_files INTEGER DEFAULT 0,
            scanned_files INTEGER DEFAULT 0,
            failed_files INTEGER DEFAULT 0,
            error_message TEXT,
            started_at TEXT,
            finished_at TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scan_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            error_message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES scan_tasks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS file_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            suggestion_type TEXT NOT NULL,
            source_path TEXT NOT NULL,
            target_path TEXT NOT NULL,
            reason TEXT,
            confidence REAL DEFAULT 0,
            conflict_status TEXT DEFAULT 'none',
            status TEXT NOT NULL DEFAULT 'pending',
            archive_root TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_file_suggestions_file_id ON file_suggestions(file_id);
        CREATE INDEX IF NOT EXISTS idx_file_suggestions_status ON file_suggestions(status);

        CREATE TABLE IF NOT EXISTS operation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL,
            file_id INTEGER,
            source_path TEXT NOT NULL,
            target_path TEXT,
            status TEXT NOT NULL,
            rollback_available INTEGER DEFAULT 1,
            executed_at TEXT NOT NULL,
            rollback_at TEXT,
            error_message TEXT,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_operation_logs_file_id ON operation_logs(file_id);
        CREATE INDEX IF NOT EXISTS idx_operation_logs_status ON operation_logs(status);

        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS file_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            text_content TEXT,
            text_length INTEGER DEFAULT 0,
            extractor_type TEXT NOT NULL,
            extract_status TEXT NOT NULL,
            error_message TEXT,
            extracted_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_file_contents_file_id ON file_contents(file_id);
        CREATE INDEX IF NOT EXISTS idx_file_contents_status ON file_contents(extract_status);

        CREATE TABLE IF NOT EXISTS extract_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            started_at TEXT,
            finished_at TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_extract_tasks_file_id ON extract_tasks(file_id);
        CREATE INDEX IF NOT EXISTS idx_extract_tasks_status ON extract_tasks(status);

        CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts USING fts5(
            file_id UNINDEXED,
            filename,
            current_path,
            text_content,
            tokenize='trigram'
        );

        CREATE TRIGGER IF NOT EXISTS idx_file_contents_fts_insert AFTER INSERT ON file_contents BEGIN
            DELETE FROM file_content_fts WHERE file_id = new.file_id;
            INSERT INTO file_content_fts(file_id, filename, current_path, text_content)
            SELECT new.file_id, f.filename, f.current_path, new.text_content
            FROM file_records f WHERE f.id = new.file_id AND new.extract_status = 'completed';
        END;

        CREATE TRIGGER IF NOT EXISTS idx_file_contents_fts_update AFTER UPDATE ON file_contents BEGIN
            DELETE FROM file_content_fts WHERE file_id = old.file_id;
            INSERT INTO file_content_fts(file_id, filename, current_path, text_content)
            SELECT new.file_id, f.filename, f.current_path, new.text_content
            FROM file_records f WHERE f.id = new.file_id AND new.extract_status = 'completed';
        END;

        CREATE TRIGGER IF NOT EXISTS idx_file_contents_fts_delete AFTER DELETE ON file_contents BEGIN
            DELETE FROM file_content_fts WHERE file_id = old.file_id;
        END;

        CREATE TRIGGER IF NOT EXISTS idx_file_records_fts_insert AFTER INSERT ON file_records BEGIN
            INSERT INTO file_content_fts(file_id, filename, current_path, text_content)
            VALUES (new.id, new.filename, new.current_path, '');
        END;

        CREATE TRIGGER IF NOT EXISTS idx_file_records_fts_update AFTER UPDATE OF filename, current_path ON file_records BEGIN
            UPDATE file_content_fts SET filename = new.filename, current_path = new.current_path WHERE file_id = new.id;
        END;

        CREATE TRIGGER IF NOT EXISTS idx_file_records_fts_delete AFTER DELETE ON file_records BEGIN
            DELETE FROM file_content_fts WHERE file_id = old.id;
        END;

        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            pattern TEXT NOT NULL,
            target_dir TEXT,
            action TEXT NOT NULL,
            priority INTEGER DEFAULT 100,
            enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_rules_enabled_priority ON rules(enabled, priority);

        CREATE TABLE IF NOT EXISTS ai_rule_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_prompt TEXT NOT NULL,
            name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            pattern TEXT NOT NULL,
            target_dir TEXT NOT NULL,
            action TEXT NOT NULL,
            priority INTEGER DEFAULT 90,
            reason TEXT,
            confidence REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'draft',
            validation_error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_ai_rule_drafts_status ON ai_rule_drafts(status);

        CREATE TABLE IF NOT EXISTS ai_classification_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            suggested_target_dir TEXT NOT NULL,
            directory_status TEXT NOT NULL DEFAULT 'proposed_new',
            confidence REAL DEFAULT 0,
            reason TEXT,
            evidence_json TEXT,
            source_context_hash TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_ai_classification_file_id ON ai_classification_suggestions(file_id);
        CREATE INDEX IF NOT EXISTS idx_ai_classification_status ON ai_classification_suggestions(status);

        CREATE TABLE IF NOT EXISTS organize_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            scope TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            summary_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_organize_plans_status ON organize_plans(status);

        CREATE TABLE IF NOT EXISTS organize_plan_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            file_id INTEGER NOT NULL,
            source_path TEXT NOT NULL,
            target_dir TEXT NOT NULL,
            target_path TEXT NOT NULL,
            directory_status TEXT NOT NULL DEFAULT 'proposed_new',
            confidence REAL DEFAULT 0,
            reason TEXT,
            evidence_json TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (plan_id) REFERENCES organize_plans(id) ON DELETE CASCADE,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_plan_items_plan_id ON organize_plan_items(plan_id);
        CREATE INDEX IF NOT EXISTS idx_plan_items_status ON organize_plan_items(status);

        CREATE TABLE IF NOT EXISTS file_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            summary TEXT NOT NULL,
            llm_provider TEXT,
            model_name TEXT,
            source_content_hash TEXT,
            status TEXT NOT NULL DEFAULT 'completed',
            error_message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_file_summaries_file_id ON file_summaries(file_id);

        CREATE TABLE IF NOT EXISTS ai_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            input_json TEXT,
            result_ref_type TEXT,
            result_ref_id INTEGER,
            total_items INTEGER DEFAULT 0,
            processed_items INTEGER DEFAULT 0,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            estimated_tokens INTEGER DEFAULT 0,
            actual_tokens INTEGER DEFAULT 0,
            estimated_cost REAL DEFAULT 0,
            started_at TEXT,
            finished_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_ai_tasks_status ON ai_tasks(status);
        CREATE INDEX IF NOT EXISTS idx_ai_tasks_type_status ON ai_tasks(task_type, status);

        CREATE TRIGGER IF NOT EXISTS idx_ai_classification_stale_on_content_update
        AFTER UPDATE OF extract_status ON file_contents
        WHEN new.extract_status = 'stale'
        BEGIN
            UPDATE ai_classification_suggestions
            SET status = 'stale',
                updated_at = CURRENT_TIMESTAMP
            WHERE file_id = new.file_id
              AND status IN ('pending', 'accepted', 'in_plan');
        END;

        CREATE TRIGGER IF NOT EXISTS idx_file_summary_stale_on_content_update
        AFTER UPDATE OF extract_status ON file_contents
        WHEN new.extract_status = 'stale'
        BEGIN
            UPDATE file_summaries
            SET status = 'stale',
                updated_at = CURRENT_TIMESTAMP
            WHERE file_id = new.file_id
              AND status = 'completed';
        END;

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS file_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            confidence REAL DEFAULT 1.0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            UNIQUE(file_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS semantic_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS semantic_group_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            file_id INTEGER NOT NULL,
            similarity REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            FOREIGN KEY (group_id) REFERENCES semantic_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (file_id) REFERENCES file_records(id) ON DELETE CASCADE,
            UNIQUE(group_id, file_id)
        );
    """)
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

    # Insert default rules if table is empty
    rule_count = conn.execute("SELECT COUNT(*) as cnt FROM rules").fetchone()["cnt"]
    if rule_count == 0:
        from ..models.scan_task import now_iso
        now = now_iso()
        default_rules = [
            # Content Keyword Rules (highest priority)
            ("学术论文", "content_keyword", "论文,毕业,开题,thesis,dissertation", "University/Thesis", "move_to", 90),
            ("财务凭证", "content_keyword", "发票,invoice,receipt,收据,税号", "Finance/Receipts", "move_to", 90),
            ("求职简历", "content_keyword", "简历,resume,curriculum vitae", "Personal/Resume", "move_to", 90),
            ("哲学经典", "content_keyword", "康德,Kant,纯粹理性批判", "Books/Philosophy", "move_to", 90),
            # Filename Keyword Rules
            ("工作报告", "filename_keyword", "报告,report,总结", "Work/Reports", "move_to", 80),
            ("屏幕截图", "filename_keyword", "照片,photo,screenshot,截图", "Images/Screenshots", "move_to", 80),
            # Extension Rules
            ("文档_PDF", "extension", ".pdf", "Documents/PDF", "move_to", 50),
            ("文档_Word", "extension", ".doc,.docx", "Documents/Word", "move_to", 50),
            ("文档_Excel", "extension", ".xls,.xlsx", "Documents/Excel", "move_to", 50),
            ("文档_PPT", "extension", ".ppt,.pptx", "Documents/PowerPoint", "move_to", 50),
            ("笔记文本", "extension", ".md,.txt", "Notes", "move_to", 50),
            ("图片文件", "extension", ".png,.jpg,.jpeg,.webp,.gif,.bmp,.svg", "Images", "move_to", 50),
            ("压缩归档", "extension", ".zip,.rar,.7z,.tar,.gz", "Archives", "move_to", 50),
            ("视频文件", "extension", ".mp4,.mov,.avi,.mkv,.webm", "Videos", "move_to", 50),
            ("音频文件", "extension", ".mp3,.wav,.flac,.aac", "Audio", "move_to", 50),
            ("代码源码", "extension", ".py,.js,.ts,.java,.cpp,.c,.h,.rs,.go", "Code", "move_to", 50),
        ]
        for r in default_rules:
            conn.execute(
                """INSERT INTO rules (name, rule_type, pattern, target_dir, action, priority, enabled, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
                (r[0], r[1], r[2], r[3], r[4], r[5], now)
            )

    conn.commit()
