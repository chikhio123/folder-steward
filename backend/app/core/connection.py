import sqlite3
import threading
from pathlib import Path

from .config import settings

_local = threading.local()

# Track which DB paths have had their schema initialized.
# Per-path tracking is critical: tests switch settings.database_path,
# and a single global bool would skip schema creation on the new path.
# Flag is set BEFORE calling init_db() to prevent recursion:
#   get_connection() → _ensure_schema() → mark path → init_db() → get_connection() (finds existing conn, path is marked → returns)
_initialized_paths: set[str] = set()
_init_lock = threading.Lock()


def _ensure_schema(db_path: str) -> None:
    """Lazily initialize schema if this db_path hasn't been seen before.
    Safe against recursion because we mark the path before calling init_db(),
    which internally calls get_connection() and will see the path is already handled.
    On failure, the path is removed from the set so the next request retries.
    """
    if db_path in _initialized_paths:
        return
    with _init_lock:
        if db_path in _initialized_paths:
            return
        _initialized_paths.add(db_path)
    try:
        from .schema import init_db
        init_db()
    except Exception:
        with _init_lock:
            _initialized_paths.discard(db_path)
        raise


def get_connection() -> sqlite3.Connection:
    """Get a thread-local SQLite connection, lazily initializing schema on first use."""
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

    _ensure_schema(db_path)
    return conn


def close_connection() -> None:
    conn = getattr(_local, "connection", None)
    if conn:
        conn.close()
        _local.connection = None


def set_in_transaction(in_tx: bool) -> None:
    _local.in_transaction = in_tx

def is_in_transaction() -> bool:
    return getattr(_local, "in_transaction", False)

class TransactionRequiredError(RuntimeError):
    pass

def require_transaction() -> None:
    if not is_in_transaction():
        raise TransactionRequiredError("Write operation requires UnitOfWork")