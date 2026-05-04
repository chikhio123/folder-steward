import hashlib
from pathlib import Path

from ..core.errors import ScanError


class HashService:
    CHUNK_SIZE = 4 * 1024 * 1024  # 4MB

    def calculate_sha256(self, path: Path) -> str:
        """Calculate SHA-256 hash with chunked reading.
        Returns hex digest string.
        Raises ScanError on I/O failure."""
        try:
            sha = hashlib.sha256()
            with path.open("rb") as f:
                while chunk := f.read(self.CHUNK_SIZE):
                    sha.update(chunk)
            return sha.hexdigest()
        except (PermissionError, FileNotFoundError, OSError) as e:
            raise ScanError(
                f"Failed to read file '{path}' for hashing: {e}"
            ) from e
