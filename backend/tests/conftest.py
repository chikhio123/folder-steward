import os
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory outside of system-protected paths."""
    # Use the project root's parent dir to avoid AppData blacklist
    project_parent = Path(__file__).resolve().parent.parent.parent  # backend/../..
    safe_base = project_parent / ".test_tmp"
    safe_base.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="fs_test_", dir=str(safe_base)))
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def temp_db():
    """Set up a temporary SQLite database for testing."""
    from app.core.config import settings
    old_path = settings.database_path

    tmp_db = tempfile.mktemp(suffix=".db", prefix="fs_test_")
    settings.database_path = tmp_db

    from app.core.database import init_db, close_connection
    init_db()
    yield tmp_db

    close_connection()
    settings.database_path = old_path
    try:
        os.unlink(tmp_db)
    except OSError:
        pass


def create_test_file(dir_path: Path, name: str, content: bytes = b"hello world") -> Path:
    """Helper to create a test file with known content."""
    path = dir_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path
