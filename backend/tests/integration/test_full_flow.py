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
from app.repositories.scan_task_repository import ScanTaskRepository


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

    def test_scan_total_files_includes_failed_files(self, temp_dir, monkeypatch):
        source = temp_dir / "scan_failures"
        source.mkdir()
        ok_file = source / "ok.txt"
        bad_file = source / "bad.txt"
        ok_file.write_bytes(b"ok")
        bad_file.write_bytes(b"bad")

        scan_service = ScanService()
        original_scan_single = scan_service._scan_single_file

        def fail_one_file(task_id, task, path, root):
            if path.name == "bad.txt":
                raise RuntimeError("forced scan failure")
            return original_scan_single(task_id, task, path, root)

        monkeypatch.setattr(scan_service, "_scan_single_file", fail_one_file)
        task = scan_service.create_scan_task(str(source))

        import time
        max_wait = 10
        while max_wait > 0:
            task = scan_service.get_task(task.id)
            if task and task.status in ("completed", "failed"):
                break
            time.sleep(0.2)
            max_wait -= 1

        assert task is not None
        assert task.status == "completed"
        assert task.scanned_files == 1
        assert task.failed_files == 1
        assert task.total_files == 2

    def test_scan_thread_respects_persisted_cancelled_status(self, temp_dir):
        source = temp_dir / "cancelled"
        source.mkdir()
        (source / "file.txt").write_bytes(b"content")

        task_repo = ScanTaskRepository()
        task = task_repo.create(str(source))
        task.status = "cancelled"
        task.finished_at = "already-cancelled"
        task_repo.update(task)

        scan_service = ScanService()
        scan_service._run_scan(task.id)

        task_after = scan_service.get_task(task.id)
        assert task_after is not None
        assert task_after.status == "cancelled"
        assert task_after.scanned_files == 0

    def test_scan_start_does_not_overwrite_concurrent_cancel(self, temp_dir, monkeypatch):
        source = temp_dir / "cancel_race"
        source.mkdir()
        (source / "file.txt").write_bytes(b"content")

        task_repo = ScanTaskRepository()
        task = task_repo.create(str(source))
        scan_service = ScanService()
        original_mark_running = scan_service.task_repo.mark_running_if_pending

        def cancel_before_start(task_id, started_at):
            cancel_task = task_repo.get(task_id)
            cancel_task.status = "cancelled"
            cancel_task.finished_at = "cancelled-before-start"
            task_repo.update(cancel_task)
            return original_mark_running(task_id, started_at)

        monkeypatch.setattr(scan_service.task_repo, "mark_running_if_pending", cancel_before_start)

        scan_service._run_scan(task.id)

        task_after = scan_service.get_task(task.id)
        assert task_after is not None
        assert task_after.status == "cancelled"
        assert task_after.scanned_files == 0

    def test_scan_complete_does_not_overwrite_concurrent_cancel(self, temp_dir, monkeypatch):
        source = temp_dir / "cancel_before_complete"
        source.mkdir()
        (source / "file.txt").write_bytes(b"content")

        scan_service = ScanService()
        original_complete = scan_service.task_repo.complete_if_running

        def cancel_before_complete(task):
            cancel_task = scan_service.task_repo.get(task.id)
            cancel_task.status = "cancelled"
            cancel_task.finished_at = "cancelled-before-complete"
            scan_service.task_repo.update(cancel_task)
            return original_complete(task)

        monkeypatch.setattr(scan_service.task_repo, "complete_if_running", cancel_before_complete)
        task = scan_service.create_scan_task(str(source))

        import time
        max_wait = 10
        while max_wait > 0:
            task = scan_service.get_task(task.id)
            if task and task.status in ("completed", "failed", "cancelled"):
                break
            time.sleep(0.2)
            max_wait -= 1

        assert task is not None
        assert task.status == "cancelled"

    def test_execute_suggestion_restores_file_if_db_logging_fails(self, temp_dir, monkeypatch):
        source_dir = temp_dir / "restore_on_failure"
        source_dir.mkdir()
        source = source_dir / "keep.txt"
        source.write_bytes(b"content")
        archive_root = temp_dir / "Archive"

        scan_service = ScanService()
        task = scan_service.create_scan_task(str(source_dir))
        import time
        max_wait = 10
        while max_wait > 0:
            task = scan_service.get_task(task.id)
            if task and task.status in ("completed", "failed"):
                break
            time.sleep(0.2)
            max_wait -= 1

        SuggestionService().generate_suggestions(str(archive_root))
        sug_repo = SuggestionRepository()
        suggestions, _ = sug_repo.list_paginated(page=1, page_size=10)
        suggestion = suggestions[0]
        target = Path(suggestion.target_path)

        op_service = OperationService()

        # Rename the table so the UPDATE fails, simulating a DB failure after move
        from app.core.database import get_connection
        conn = get_connection()
        conn.execute("ALTER TABLE file_records RENAME TO file_records_temp")

        try:
            result = op_service.execute_suggestions([suggestion.id])
        finally:
            conn.execute("ALTER TABLE file_records_temp RENAME TO file_records")

        assert result["success_count"] == 0

        assert result["success_count"] == 0
        assert result["failed_count"] == 1
        assert source.exists()
        assert not target.exists()
        rec = FileRepository().get(suggestion.file_id)
        assert rec is not None
        assert rec.current_path == str(source)

    def test_execute_old_suggestion_uses_its_archive_root_snapshot(self, temp_dir):
        source_a = temp_dir / "batch_a"
        source_b = temp_dir / "batch_b"
        source_a.mkdir()
        source_b.mkdir()
        file_a = source_a / "a.txt"
        file_b = source_b / "b.txt"
        file_a.write_bytes(b"a")
        file_b.write_bytes(b"b")
        archive_a = temp_dir / "ArchiveA"
        archive_b = temp_dir / "ArchiveB"

        scan_service = ScanService()
        for source in (source_a, source_b):
            task = scan_service.create_scan_task(str(source))
            import time
            max_wait = 10
            while max_wait > 0:
                task = scan_service.get_task(task.id)
                if task and task.status in ("completed", "failed"):
                    break
                time.sleep(0.2)
                max_wait -= 1

        sug_service = SuggestionService()
        sug_service.generate_suggestions(str(archive_a))
        sug_repo = SuggestionRepository()
        suggestions_a, _ = sug_repo.list_paginated(page=1, page_size=20)
        old_suggestion = next(s for s in suggestions_a if s.source_path == str(file_a))

        # simulate changing the global archive root
        from app.core.database import get_connection
        from app.models.scan_task import now_iso
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            ("archive_root", str(archive_b), now_iso())
        )
        conn.commit()

        result = OperationService().execute_suggestions([old_suggestion.id])

        assert result["success_count"] == 1
        assert (archive_a / "Others" / "NoExtension" / "a.txt").exists() or (archive_a / "Notes" / "a.txt").exists()
