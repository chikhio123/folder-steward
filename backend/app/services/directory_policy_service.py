import os
from pathlib import Path

class DirectoryPolicyService:
    def evaluate(self, target_dir: str, archive_root_str: str) -> str:
        """
        Evaluates a target directory suggested by AI.
        Returns one of: 'existing', 'proposed_new', 'invalid'
        """
        if not target_dir or not target_dir.strip():
            return "invalid"

        target_dir = target_dir.strip().replace("\\", "/")

        # 1. Reject empty paths, absolute paths, or paths with parent traversal
        if target_dir.startswith("/") or ":" in target_dir or ".." in target_dir:
            return "invalid"

        archive_root = Path(archive_root_str).resolve()

        # 2. Check if it resolves within archive_root safely
        try:
            target_path = (archive_root / target_dir).resolve()
            if not target_path.is_relative_to(archive_root):
                return "invalid"
            if target_path == archive_root:
                return "invalid" # Root itself is not a valid classification target
        except Exception:
            return "invalid"

        # 3. Check if exists
        if target_path.exists():
            if target_path.is_dir():
                return "existing"
            else:
                return "invalid" # Conflicts with a file

        return "proposed_new"
