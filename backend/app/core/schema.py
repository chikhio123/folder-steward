from .connection import get_connection
from .schema_sql import SCHEMA_SQL
from .migrations import run_lightweight_migrations
from .seeds import seed_default_rules

def init_db() -> None:
    """Create all tables if they don't exist.
    Uses ensure_schema=False to avoid recursion when called from _ensure_schema.
    """
    conn = get_connection(ensure_schema=False)
    conn.executescript(SCHEMA_SQL)
    run_lightweight_migrations(conn)
    seed_default_rules(conn)
    conn.commit()
