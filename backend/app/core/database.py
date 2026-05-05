import sqlite3
import threading
from pathlib import Path

from .config import settings

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get a thread-local SQLite connection."""
    conn = getattr(_local, "connection", None)
    if conn is None:
        db_path = Path(settings.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.connection = conn
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
            FOREIGN KEY (task_id) REFERENCES scan_tasks(id)
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
            FOREIGN KEY (file_id) REFERENCES file_records(id)
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
            FOREIGN KEY (file_id) REFERENCES file_records(id)
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
            FOREIGN KEY (file_id) REFERENCES file_records(id)
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
            FOREIGN KEY (file_id) REFERENCES file_records(id)
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
    """)
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(file_suggestions)").fetchall()
    }
    if "archive_root" not in columns:
        conn.execute("ALTER TABLE file_suggestions ADD COLUMN archive_root TEXT")
    conn.commit()
