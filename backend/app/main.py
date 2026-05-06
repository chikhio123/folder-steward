from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.database import init_db
from .services.extract_service import ExtractService

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ExtractService.cleanup_ghost_tasks()
    yield

app = FastAPI(title="Folder Steward", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# Register routes will be imported and added in later blocks
from .api.scan_tasks import router as scan_router
from .api.files import router as files_router
from .api.duplicates import router as duplicates_router
from .api.suggestions import router as suggestions_router
from .api.operations import router as operations_router
from .api.settings import router as settings_router
from .api.dashboard import router as dashboard_router
from .api.extract_tasks import router as extract_tasks_router
from .api.file_contents import router as file_contents_router
from .api.search import router as search_router
from .api.rules import router as rules_router
from .api.ai_rules import router as ai_rules_router

app.include_router(scan_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(duplicates_router, prefix="/api")
app.include_router(suggestions_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(extract_tasks_router, prefix="/api")
app.include_router(file_contents_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(rules_router, prefix="/api")
app.include_router(ai_rules_router, prefix="/api")
