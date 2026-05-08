# Backend Modularity Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the backend to remove module-level repository instantiation and raw SQL from API routers, improving modularity and testability.

**Architecture:** Introduce `SettingsRepository` for fetching/updating application settings, replacing raw `get_connection()` calls in `smart_organize.py`. Use FastAPI's `Depends` for dependency injection of `FileRepository` in `files.py` and `SettingsRepository` in `smart_organize.py`. All dependencies will be registered in `app/dependencies.py`.

**Tech Stack:** Python, FastAPI, SQLite

---

### Task 1: Create SettingsRepository

**Files:**
- Create: `backend/app/repositories/settings_repository.py`
- Test: `backend/tests/repositories/test_settings_repository.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/repositories/test_settings_repository.py
import pytest
from app.repositories.settings_repository import SettingsRepository
from app.core.database import get_connection

@pytest.fixture(autouse=True)
def setup_db():
    conn = get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)")
    conn.execute("DELETE FROM app_settings")
    conn.commit()

def test_settings_repository_get_and_set():
    repo = SettingsRepository()
    
    # Test get missing key
    assert repo.get("missing_key") is None
    
    # Test set key
    repo.set("my_key", "my_value")
    
    # Test get existing key
    assert repo.get("my_key") == "my_value"
    
    # Test update existing key
    repo.set("my_key", "new_value")
    assert repo.get("my_key") == "new_value"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/repositories/test_settings_repository.py -v`
Expected: FAIL with ModuleNotFoundError or ImportError for SettingsRepository.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/repositories/settings_repository.py
from app.core.database import get_connection
from app.models.scan_task import now_iso

class SettingsRepository:
    def get(self, key: str) -> str | None:
        conn = get_connection()
        row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None

    def set(self, key: str, value: str) -> None:
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, now_iso())
        )
        conn.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/repositories/test_settings_repository.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add tests/repositories/test_settings_repository.py app/repositories/settings_repository.py
git commit -m "feat: add SettingsRepository"
```

### Task 2: Add Dependencies to `dependencies.py`

**Files:**
- Modify: `backend/app/dependencies.py:44-50`
- Test: `backend/tests/test_dependencies.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_dependencies.py
from app.dependencies import get_settings_repository, get_file_repository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.file_repository import FileRepository

def test_dependency_providers():
    settings_repo = get_settings_repository()
    assert isinstance(settings_repo, SettingsRepository)

    file_repo = get_file_repository()
    assert isinstance(file_repo, FileRepository)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_dependencies.py -v`
Expected: FAIL with ImportError for `get_settings_repository` and `get_file_repository`.

- [ ] **Step 3: Write minimal implementation**

```python
# Append to backend/app/dependencies.py
from .repositories.settings_repository import SettingsRepository
from .repositories.file_repository import FileRepository

def get_settings_repository() -> SettingsRepository:
    return SettingsRepository()

def get_file_repository() -> FileRepository:
    return FileRepository()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_dependencies.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add tests/test_dependencies.py app/dependencies.py
git commit -m "refactor: add SettingsRepository and FileRepository to dependencies"
```

### Task 3: Refactor `app/api/files.py` to use `Depends`

**Files:**
- Modify: `backend/app/api/files.py:1-20`
- Test: `backend/tests/api/test_files.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/api/test_files.py
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_file_repository
from unittest.mock import MagicMock

client = TestClient(app)

def test_list_files_uses_dependency():
    mock_repo = MagicMock()
    mock_repo.list_paginated.return_value = ([], 0)
    app.dependency_overrides[get_file_repository] = lambda: mock_repo
    
    response = client.get("/files")
    
    assert response.status_code == 200
    mock_repo.list_paginated.assert_called_once()
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/api/test_files.py -v`
Expected: FAIL because `mock_repo.list_paginated` won't be called since the router uses the global module-level `FileRepository` instead of the dependency override.

- [ ] **Step 3: Write minimal implementation**

```python
# Replace in backend/app/api/files.py lines 1-20
from fastapi import APIRouter, Query, Depends
from typing import Optional

from ..repositories.file_repository import FileRepository
from ..schemas.file_schema import FileRecordResponse, FileListResponse
from ..dependencies import get_file_repository

router = APIRouter(tags=["files"])

@router.get("/files", response_model=FileListResponse)
def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    extension: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    duplicated: Optional[bool] = Query(None),
    sort_by: str = Query("modified_at"),
    sort_order: str = Query("desc"),
    file_repo: FileRepository = Depends(get_file_repository),
):
    records, total = file_repo.list_paginated(
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/api/test_files.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add tests/api/test_files.py app/api/files.py
git commit -m "refactor: use Depends for FileRepository in files API"
```

### Task 4: Refactor `app/api/smart_organize.py`

**Files:**
- Modify: `backend/app/api/smart_organize.py`
- Test: `backend/tests/api/test_smart_organize_refactor.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/api/test_smart_organize_refactor.py
import json
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_settings_repository, get_ai_task_queue_service
from unittest.mock import MagicMock

client = TestClient(app)

def test_classify_uses_settings_repository():
    mock_settings = MagicMock()
    mock_settings.get.return_value = "/mock/archive"
    app.dependency_overrides[get_settings_repository] = lambda: mock_settings
    
    mock_queue = MagicMock()
    mock_queue.enqueue_task.return_value = 1
    app.dependency_overrides[get_ai_task_queue_service] = lambda: mock_queue

    response = client.post("/ai/classify", json={"file_ids": [1, 2]})
    
    assert response.status_code == 200
    mock_settings.get.assert_called_with("archive_root")
    app.dependency_overrides.clear()

def test_update_exclude_paths_uses_settings_repository():
    mock_settings = MagicMock()
    app.dependency_overrides[get_settings_repository] = lambda: mock_settings
    
    response = client.post("/ai/exclude-paths", json={"exclude_paths": ["/mock/path"]})
    
    assert response.status_code == 200
    mock_settings.set.assert_called_once()
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/api/test_smart_organize_refactor.py -v`
Expected: FAIL because `mock_settings.get` and `mock_settings.set` are not called.

- [ ] **Step 3: Write minimal implementation**

```python
# Add to imports in backend/app/api/smart_organize.py
from ..dependencies import (
    get_ai_classification_service,
    get_organize_plan_service,
    get_path_protection_service,
    get_ai_task_queue_service,
    get_settings_repository
)
from ..repositories.settings_repository import SettingsRepository

# Update create_classification_tasks signature and body in backend/app/api/smart_organize.py
@router.post("/ai/classify", response_model=AIClassifyResponse)
def create_classification_tasks(
    body: AIClassifyRequest,
    class_service: AIClassificationService = Depends(get_ai_classification_service),
    path_protection: PathProtectionService = Depends(get_path_protection_service),
    queue_service: AITaskQueueService = Depends(get_ai_task_queue_service),
    settings_repo: SettingsRepository = Depends(get_settings_repository)
):
    if not body.file_ids:
        raise HTTPException(400, "No files specified")

    archive_root = settings_repo.get("archive_root") or ""

    if not archive_root:
        raise HTTPException(400, "archive_root is not configured in settings")

    # ... rest of the function remains the same ...

# Update update_exclude_paths signature and body in backend/app/api/smart_organize.py
@router.post("/ai/exclude-paths", response_model=ExcludePathsResponse)
def update_exclude_paths(
    body: ExcludePathsRequest,
    service: PathProtectionService = Depends(get_path_protection_service),
    settings_repo: SettingsRepository = Depends(get_settings_repository)
):
    paths = body.exclude_paths
    if not isinstance(paths, list):
        raise HTTPException(400, "exclude_paths must be an array")
    normalized = [service.normalize_path(p) for p in paths if isinstance(p, str) and p.strip()]

    import json
    settings_repo.set(service.SETTING_KEY, json.dumps(normalized))
    
    return ExcludePathsResponse(status="success", exclude_paths=normalized)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/api/test_smart_organize_refactor.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend
git add tests/api/test_smart_organize_refactor.py app/api/smart_organize.py
git commit -m "refactor: remove raw SQL from smart_organize API, use SettingsRepository"
```
