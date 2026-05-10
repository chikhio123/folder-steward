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


def set_in_transaction(in_tx: bool) -> None:
    _local.in_transaction = in_tx

def is_in_transaction() -> bool:
    return getattr(_local, "in_transaction", False)

class TransactionRequiredError(RuntimeError):
    pass

def require_transaction() -> None:
    if not is_in_transaction():
        raise TransactionRequiredError("Write operation requires UnitOfWork")