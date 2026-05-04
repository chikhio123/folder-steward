import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    database_path: str = field(default_factory=lambda: os.getenv(
        "FS_DATABASE_PATH",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "folder_steward.db"),
    ))
    archive_root: str = field(default_factory=lambda: os.getenv("FS_ARCHIVE_ROOT", ""))
    scan_hidden_files: bool = False
    max_file_size_for_hash: int = 100 * 1024 * 1024  # 100 MB
    skip_system_directories: bool = True


settings = Settings()
