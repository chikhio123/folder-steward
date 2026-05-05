import threading
from typing import Optional

from ..models.extract_task import ExtractTask
from ..models.scan_task import now_iso
from ..repositories.extract_task_repository import ExtractTaskRepository
from ..repositories.file_repository import FileRepository
from ..repositories.file_content_repository import FileContentRepository

class ExtractService:
    def __init__(self) -> None:
        self.task_repo = ExtractTaskRepository()
        self.file_repo = FileRepository()
        self.content_repo = FileContentRepository()
        self._running_tasks: dict[int, threading.Thread] = {}

    def create_extract_tasks(self, file_ids: Optional[list[int]] = None, mode: str = "missing_only") -> tuple[int, int]:
        # Dummy implementation for M1
        # In a real scenario, this would query file_records based on the mode and file_ids,
        # checking extensions (txt, md, pdf, docx), and create tasks.

        # For now, just pretend we processed 0 files
        created = 0
        skipped = 0

        # TODO: Implement actual logic in Milestone 2
        return created, skipped

    def run_extract_task(self, task_id: int) -> None:
        pass
