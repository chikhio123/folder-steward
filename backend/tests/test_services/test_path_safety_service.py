import os
import platform
from pathlib import Path

import pytest

from app.services.path_safety_service import PathSafetyService
from app.core.errors import PathSafetyError

IS_WINDOWS = platform.system() == "Windows"


class TestPathSafetyService:
    def setup_method(self):
        self.service = PathSafetyService()

    # --- validate_scan_root ---

    def test_validate_scan_root_valid(self, temp_dir):
        self.service.validate_scan_root(temp_dir)  # should not raise

    def test_validate_scan_root_nonexistent(self, temp_dir):
        path = temp_dir / "nonexistent"
        with pytest.raises(PathSafetyError, match="does not exist"):
            self.service.validate_scan_root(path)

    def test_validate_scan_root_relative(self, temp_dir):
        import os
        old = os.getcwd()
        os.chdir(temp_dir)
        try:
            with pytest.raises(PathSafetyError, match="not absolute"):
                self.service.validate_scan_root(Path("."))
        finally:
            os.chdir(old)

    @pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific test")
    def test_validate_scan_root_windows_system_dir(self):
        with pytest.raises(PathSafetyError, match="system-sensitive"):
            self.service.validate_scan_root(Path("C:/Windows"))

    @pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific test")
    def test_validate_scan_root_windows_drive_root(self):
        # C:/ is no longer blocked (that would block all C:\ scanning),
        # but specific system directories still are
        self.service.validate_scan_root(Path("C:/Users"))  # should not raise

    @pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific test")
    def test_validate_scan_root_windows_program_files(self):
        with pytest.raises(PathSafetyError, match="system-sensitive"):
            self.service.validate_scan_root(Path("C:/Program Files"))

    # --- is_system_sensitive_path ---

    @pytest.mark.skipif(not IS_WINDOWS, reason="Windows-specific test")
    def test_is_system_sensitive_windows(self):
        assert self.service.is_system_sensitive_path(Path("C:/Windows"))
        assert self.service.is_system_sensitive_path(Path("C:/Program Files"))
        assert not self.service.is_system_sensitive_path(Path("D:/Users"))

    def test_is_system_sensitive_normal_path(self, temp_dir):
        assert not self.service.is_system_sensitive_path(temp_dir)

    # --- validate_move ---

    def test_validate_move_valid(self, temp_dir):
        source = temp_dir / "source.txt"
        source.write_bytes(b"test")
        target = temp_dir / "target.txt"

        self.service.validate_move(source, target)  # should not raise

    def test_validate_move_source_missing(self, temp_dir):
        source = temp_dir / "missing.txt"
        target = temp_dir / "target.txt"

        with pytest.raises(PathSafetyError, match="does not exist"):
            self.service.validate_move(source, target)

    def test_validate_move_target_exists(self, temp_dir):
        source = temp_dir / "source.txt"
        source.write_bytes(b"test")
        target = temp_dir / "target.txt"
        target.write_bytes(b"existing")

        with pytest.raises(PathSafetyError, match="already exists"):
            self.service.validate_move(source, target)
