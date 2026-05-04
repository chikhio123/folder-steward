class FolderStewardError(Exception):
    """Base error for all application errors."""


class ScanError(FolderStewardError):
    """Raised when a file cannot be scanned."""


class PathSafetyError(FolderStewardError):
    """Raised when a path fails safety validation."""


class OperationError(FolderStewardError):
    """Raised when a file operation fails."""


class RollbackError(FolderStewardError):
    """Raised when a rollback operation fails."""


class DatabaseError(FolderStewardError):
    """Raised when a database operation fails."""
