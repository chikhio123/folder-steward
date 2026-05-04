from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ScanTask:
    id: Optional[int] = None
    root_path: str = ""
    status: str = "pending"
    total_files: int = 0
    scanned_files: int = 0
    failed_files: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: str = ""


@dataclass
class ScanError:
    id: Optional[int] = None
    task_id: int = 0
    file_path: str = ""
    error_message: str = ""
    created_at: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
