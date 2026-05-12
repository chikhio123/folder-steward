import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.config import settings
from app.core.connection import get_connection, _initialized_paths


@pytest.fixture(autouse=True)
def reset_initialized_paths():
    yield
    db_path = str(Path(settings.database_path))
    _initialized_paths.discard(db_path)


def test_lazy_init_concurrency_safety():
    """Two threads race to call get_connection() on a fresh DB path.
    init_db() must execute exactly once. The second thread must not
    skip schema initialization."""
    import app.core.schema as schema_mod

    db_path = str(Path(settings.database_path))
    _initialized_paths.discard(db_path)

    init_call_count = 0
    init_is_running = threading.Event()
    let_init_finish = threading.Event()

    original_init_db = schema_mod.init_db

    results = [None, None]

    def delayed_init_db():
        nonlocal init_call_count
        init_call_count += 1
        init_is_running.set()
        assert let_init_finish.wait(timeout=10), "Timeout waiting for init to proceed"
        original_init_db()

    def thread_func(idx):
        try:
            conn = get_connection()
            # Quick sanity: the DB should be fully initialized
            conn.execute("SELECT COUNT(*) FROM file_records").fetchone()
            results[idx] = True
        except Exception as e:
            results[idx] = e

    schema_mod.init_db = delayed_init_db
    try:
        t1 = threading.Thread(target=thread_func, args=(0,))
        t2 = threading.Thread(target=thread_func, args=(1,))

        t1.start()
        assert init_is_running.wait(timeout=10), "Thread 1 didn't enter init_db"

        t2.start()
        time.sleep(0.2)

        let_init_finish.set()

        t1.join(timeout=10)
        t2.join(timeout=10)

        assert init_call_count == 1, (
            f"init_db called {init_call_count} times, expected 1"
        )
        assert results[0] is True, f"Thread 1 failed: {results[0]}"
        assert results[1] is True, f"Thread 2 failed: {results[1]}"
    finally:
        schema_mod.init_db = original_init_db
        _initialized_paths.discard(db_path)
