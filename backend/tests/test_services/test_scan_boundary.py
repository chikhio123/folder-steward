import pytest
import tempfile
from pathlib import Path
from app.services.scan_service import ScanService
from app.models.file_record import FileRecord
from app.core.database import init_db, get_connection
from app.core.uow import UnitOfWork

def test_cleanup_missing_files_boundary():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM file_records")
    conn.commit()

    svc = ScanService()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # We want to test root = tmp/archive
        # and record path = tmp/archive_old/a.txt
        root = tmp / "archive"
        root.mkdir()

        false_root = tmp / "archive_old"
        false_root.mkdir()

        # We simulate that a.txt doesn't exist on disk,
        # so if the boundary check fails, it WOULD be marked deleted.
        false_path = false_root / "a.txt"

        rec = FileRecord(
            original_path=str(false_path),
            current_path=str(false_path),
            filename="a.txt",
            size_bytes=10,
            status="active"
        )
        with UnitOfWork():
            file_id = svc.file_repo.create(rec)

        # Run cleanup on 'root'
        cleaned = svc._cleanup_missing_files(root)

        # It should NOT clean false_path because it's not under root,
        # even though it starts with the same string
        assert cleaned == 0

        db_rec = svc.file_repo.get(file_id)
        assert db_rec.status == "active"
