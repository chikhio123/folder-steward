import os
from pathlib import Path
from dataclasses import dataclass, field

def get_default_db_path() -> str:
    if os.getenv("FS_DATABASE_PATH"):
        return os.getenv("FS_DATABASE_PATH")

    # 存放在用户目录，避免在代码目录里生成数据库
    app_dir = Path.home() / ".folder-steward"
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir / "folder_steward.db")

@dataclass
class Settings:
    database_path: str = field(default_factory=get_default_db_path)
    archive_root: str = field(default_factory=lambda: os.getenv("FS_ARCHIVE_ROOT", ""))
    scan_hidden_files: bool = False
    max_file_size_for_hash: int = 100 * 1024 * 1024  # 100 MB
    skip_system_directories: bool = True


settings = Settings()
