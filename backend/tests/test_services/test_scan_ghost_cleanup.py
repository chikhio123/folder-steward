import pytest
from app.services.scan_service import ScanService
from app.repositories.scan_task_repository import ScanTaskRepository
from app.models.scan_task import ScanTask
from app.core.database import init_db, get_connection
from app.core.uow import UnitOfWork

@pytest.fixture(autouse=True)
def setup_scan_tasks():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM scan_tasks")
    conn.commit()

def test_scan_service_cleanup_ghost_tasks():
    repo = ScanTaskRepository()

    with UnitOfWork():
        t_pending = repo.create("C:/pending")
        t_running = repo.create("C:/running")
        repo.mark_running_if_pending(t_running.id, "2026-05-10T00:00:00")

        t_completed = repo.create("C:/completed")
        t_completed.status = "completed"
        repo.update(t_completed)

        t_cancelled = repo.create("C:/cancelled")
        t_cancelled.status = "cancelled"
        repo.update(t_cancelled)

        t_failed = repo.create("C:/failed")
        t_failed.status = "failed"
        repo.update(t_failed)

    ScanService.cleanup_ghost_tasks()

    # Check results
    res_pending = repo.get(t_pending.id)
    assert res_pending.status == "failed"
    assert "Process terminated unexpectedly" in res_pending.error_message
    assert res_pending.finished_at is not None

    res_running = repo.get(t_running.id)
    assert res_running.status == "failed"
    assert "Process terminated unexpectedly" in res_running.error_message
    assert res_running.finished_at is not None

    # Others should remain unchanged
    res_completed = repo.get(t_completed.id)
    assert res_completed.status == "completed"

    res_cancelled = repo.get(t_cancelled.id)
    assert res_cancelled.status == "cancelled"

    res_failed = repo.get(t_failed.id)
    assert res_failed.status == "failed"
    assert res_failed.error_message is None # because we didn't set one on creation
