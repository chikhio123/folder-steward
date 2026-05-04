import os
import platform
from pathlib import Path

from ..core.errors import PathSafetyError


class PathSafetyService:
    """Service for validating path safety for file operations."""

    _IS_WINDOWS: bool = platform.system() == "Windows"

    def __init__(self) -> None:
        self._system_paths = self._build_system_paths()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_scan_root(self, path: Path) -> None:
        """Validate path for scanning.

        Checks:
            - path exists
            - path is absolute
            - resolved path is not a system-sensitive directory

        Raises PathSafetyError on any failure.
        """
        if not path.exists():
            raise PathSafetyError(f"Path does not exist: {path}")

        if not path.is_absolute():
            raise PathSafetyError(f"Path is not absolute: {path}")

        resolved = self._resolve_safe(path)

        if self.is_system_sensitive_path(resolved):
            raise PathSafetyError(
                f"Path is system-sensitive and cannot be scanned: {path}"
            )

    def validate_move(self, source: Path, target: Path) -> None:
        """Validate a file move operation.

        Checks:
            - source exists
            - target parent directory exists and is writable
            - target does not already exist

        Raises PathSafetyError on any failure.
        """
        if not source.exists():
            raise PathSafetyError(f"Source path does not exist: {source}")

        target_parent = target.parent
        if not target_parent.exists():
            raise PathSafetyError(
                f"Target parent directory does not exist: {target_parent}"
            )
        if not os.access(str(target_parent), os.W_OK):
            raise PathSafetyError(
                f"Target parent directory is not writable: {target_parent}"
            )

        if target.exists():
            raise PathSafetyError(f"Target path already exists: {target}")

        if self.is_system_sensitive_path(target):
            raise PathSafetyError(f"Target path is system-sensitive: {target}")

    def is_system_sensitive_path(self, path: Path) -> bool:
        """Check whether *path* starts with any known system path.

        On Windows the comparison is case-insensitive; on other platforms it
        is case-sensitive.  Checks both the surface path and the real path
        (following symlinks/junctions) to prevent bypass via links.
        """
        candidates = []
        try:
            candidates.append(self._resolve_safe(path))
        except (OSError, RuntimeError):
            pass

        # Also check the real path (follows symlinks/junctions) to prevent bypass
        try:
            real = Path(os.path.realpath(str(path)))
            candidates.append(real)
        except (OSError, RuntimeError):
            pass

        for resolved in candidates:
            if self._path_matches_system(resolved):
                return True

        return False

    def _path_matches_system(self, resolved: Path) -> bool:
        sep = os.sep
        resolved_str = str(resolved).rstrip("\\/") + sep

        sep = os.sep
        check_str = resolved_str.rstrip("\\/") + sep
        for sys_path in self._system_paths:
            sys_str = str(sys_path).rstrip("\\/") + sep
            if self._IS_WINDOWS:
                if check_str.casefold().startswith(sys_str.casefold()):
                    return True
            else:
                if check_str.startswith(sys_str):
                    return True

        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_safe(path: Path) -> Path:
        """Make *path* absolute and normalized without following symlinks.

        This is the method we use everywhere instead of Path.resolve()
        (which follows symlinks) or Path.absolute() (which may not
        normalise ``..`` components on all Python 3.13 builds).
        """
        return Path(os.path.normpath(str(path.absolute())))

    @classmethod
    def _build_system_paths(cls) -> list[Path]:
        """Assemble the list of system-sensitive paths for the current OS.

        Windows paths are only included when running on Windows.  Unix paths
        are always included (they are harmless no-ops on non-Unix platforms).
        """
        paths: list[Path] = []

        # -- Windows (case-insensitive on disk) ---------------------------
        if cls._IS_WINDOWS:
            username = os.environ.get("USERNAME", "")
            paths.extend(
                [
                    Path("C:/Windows"),
                    Path("C:/Program Files"),
                    Path("C:/Program Files (x86)"),
                    Path(f"C:/Users/{username}/AppData"),
                ]
            )

        # -- Unix / macOS --------------------------------------------------
        # On Windows, Path("/") resolves to the current drive root.
        # Always including these would block all paths on the current drive.
        if not cls._IS_WINDOWS:
            paths.extend(
                [
                    Path("/"),
                    Path("/bin"),
                    Path("/boot"),
                    Path("/dev"),
                    Path("/etc"),
                    Path("/proc"),
                    Path("/sys"),
                    Path("/usr"),
                    Path("/var"),
                    Path("/System"),
                    Path("/Library"),
                    Path("/private"),
                ]
            )

        # Resolve every entry to an absolute, normalised form (no symlinks).
        resolved: list[Path] = []
        for p in paths:
            try:
                resolved.append(cls._resolve_safe(p))
            except (OSError, RuntimeError):
                resolved.append(p)

        return resolved
