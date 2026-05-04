import hashlib

from app.services.hash_service import HashService
from app.core.errors import ScanError


class TestHashService:
    def setup_method(self):
        self.service = HashService()

    def test_calculate_sha256_known_content(self, temp_dir):
        file_path = temp_dir / "test.txt"
        content = b"hello world"
        file_path.write_bytes(content)

        expected = hashlib.sha256(content).hexdigest()
        result = self.service.calculate_sha256(file_path)

        assert result == expected

    def test_calculate_sha256_empty_file(self, temp_dir):
        file_path = temp_dir / "empty.txt"
        file_path.write_bytes(b"")

        expected = hashlib.sha256(b"").hexdigest()
        result = self.service.calculate_sha256(file_path)

        assert result == expected

    def test_calculate_sha256_large_file(self, temp_dir):
        file_path = temp_dir / "large.bin"
        content = b"A" * (10 * 1024 * 1024)  # 10 MB
        file_path.write_bytes(content)

        result = self.service.calculate_sha256(file_path)
        expected = hashlib.sha256(content).hexdigest()

        assert result == expected

    def test_calculate_sha256_binary_file(self, temp_dir):
        file_path = temp_dir / "data.bin"
        content = bytes(range(256))
        file_path.write_bytes(content)

        result = self.service.calculate_sha256(file_path)
        expected = hashlib.sha256(content).hexdigest()

        assert result == expected

    def test_calculate_sha256_nonexistent_file(self, temp_dir):
        file_path = temp_dir / "does_not_exist.txt"

        import pytest
        with pytest.raises(ScanError):
            self.service.calculate_sha256(file_path)
