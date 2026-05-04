"""End-to-end integration test: scan → suggest → execute → rollback."""
import os
from pathlib import Path

import pytest

from app.core.database import get_connection
from app.services.scan_service import ScanService
from app.services.suggestion_service import SuggestionService
from app.services.operation_service import OperationService
from app.repositories.file_repository import FileRepository
from app.repositories.suggestion_repository import SuggestionRepository
from app.repositories.operation_log_repository import OperationLogRepository


@pytest.fixture(autouse=True)
def setup_db(temp_db):
    """Use the temporary DB for all tests in this module."""
    yield


class TestFullFlow:
    """Test the complete scan → suggest → execute → rollback pipeline."""

    def create_test_files(self, base_dir: Path):
        """Create a realistic set of test files."""
        files = {
            "report.pdf": b"pdf content " * 100,
            "photo.png": b"png content " * 50,
            "notes.txt": b"some notes here",
            "毕业论文终版.docx": b"thesis content " * 200,
            "archive.zip": b"zip content " * 30,
            "script.py": b"print('hello')",
            "Kant_CPR.pdf": b"philosophy content " * 150,
            "receipt.jpg": b"receipt image " * 20,
        }
        created = []
        for name, content in files.items():
            path = base_dir / name
            path.write_bytes(content)
            created.append(path)
        return created

    def test_full_pipeline(self, temp_dir):
        source_dir = temp_dir / "Downloads"
        source_dir.mkdir()
        archive_root = temp_dir / "Archive"

        self.create_test_files(source_dir)

        # === Step 1: Scan ===
        scan_service = ScanService()
        task = scan_service.create_scan_task(str(source_dir))

        # Wait for scan to complete
        import time
        max_wait = 30
        while max_wait > 0:
            task = scan_service.get_task(task.id)
            if task and task.status in ("completed", "failed"):
                break
            time.sleep(0.5)
            max_wait -= 1

        assert task is not None
        assert task.status == "completed", f"Scan failed: {task.error_message}"
        assert task.total_files == 8

        # Verify files were indexed
        file_repo = FileRepository()
        assert file_repo.count() == 8

        # === Step 2: Generate suggestions ===
        suggestion_service = SuggestionService()
        created, skipped = suggestion_service.generate_suggestions(str(archive_root))

        assert created == 8
        assert skipped == 0

        # Verify suggestions
        sug_repo = SuggestionRepository()
        pdf_suggestions, _ = sug_repo.list_paginated(page=1, page_size=100)
        assert len(pdf_suggestions) == 8

        # === Step 3: Execute suggestions ===
        all_sug, _ = sug_repo.list_paginated(page=1, page_size=100)
        sug_ids = [s.id for s in all_sug]
        assert len(sug_ids) == 8

        op_service = OperationService()
        result = op_service.execute_suggestions(sug_ids)

        assert result["success_count"] == 8
        assert result["failed_count"] == 0

        # Verify files were moved
        for sug in all_sug:
            assert not Path(sug.source_path).exists(), f"Source still exists: {sug.source_path}"
            assert Path(sug.target_path).exists(), f"Target missing: {sug.target_path}"

        # Verify DB paths were updated
        for sug in all_sug:
            rec = file_repo.get(sug.file_id)
            assert rec is not None
            assert rec.current_path == sug.target_path

        # === Step 4: Rollback ===
        op_repo = OperationLogRepository()
        ops, _ = op_repo.list_paginated(page=1, page_size=100)
        move_ops = [o for o in ops if o.operation_type == "move" and o.rollback_available]

        # Rollback all operations
        for op in move_ops:
            result = op_service.rollback_operation(op.id)
            assert result["status"] == "rolled_back"

        # Verify files returned to original locations
        for sug in all_sug:
            assert Path(sug.source_path).exists(), f"Rollback failed: {sug.source_path}"
            assert not Path(sug.target_path).exists(), f"Rollback left file: {sug.target_path}"

        # Verify DB paths were restored
        for sug in all_sug:
            rec = file_repo.get(sug.file_id)
            assert rec is not None
            assert rec.current_path == sug.source_path

    def test_scan_empty_directory(self, temp_dir):
        source = temp_dir / "empty"
        source.mkdir()

        scan_service = ScanService()
        task = scan_service.create_scan_task(str(source))

        import time
        max_wait = 10
        while max_wait > 0:
            task = scan_service.get_task(task.id)
            if task and task.status in ("completed", "failed"):
                break
            time.sleep(0.5)
            max_wait -= 1

        assert task is not None
        assert task.status == "completed"
        assert task.total_files == 0
        assert task.scanned_files == 0

        file_repo = FileRepository()
        assert file_repo.count() == 0

    def test_execute_partial_failure(self, temp_dir):
        """One failed suggestion should not block others."""
        source_dir = temp_dir / "partial"
        source_dir.mkdir()
        archive_root = temp_dir / "Archive"

        # Create two files
        (source_dir / "keep.txt").write_bytes(b"keep me")
        missing = source_dir / "missing.txt"
        missing.write_bytes(b"gone soon")

        # Scan
        scan_service = ScanService()
        task = scan_service.create_scan_task(str(source_dir))
        import time
        max_wait = 10
        while max_wait > 0:
            task = scan_service.get_task(task.id)
            if task and task.status in ("completed", "failed"):
                break
            time.sleep(0.5)
            max_wait -= 1

        # Generate suggestions
        sug_service = SuggestionService()
        sug_service.generate_suggestions(str(archive_root))

        # Delete one file before executing
        missing.unlink()

        # Execute all
        sug_repo = SuggestionRepository()
        all_sug, _ = sug_repo.list_paginated(page=1, page_size=100)
        op_service = OperationService()
        result = op_service.execute_suggestions([s.id for s in all_sug])

        assert result["success_count"] == 1
        assert result["failed_count"] == 1

        # The surviving file should have been moved (.txt → Notes)
        assert (archive_root / "Notes" / "keep.txt").exists()
