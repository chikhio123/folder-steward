from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Initialize DB first, before importing routers that instantiate services
from .core.database import init_db, close_connection
init_db()

from .services.extract_service import ExtractService
from .services.scan_service import ScanService
from .services.ai_task_queue_service import AITaskQueueService
# Initialize other things if needed

@asynccontextmanager
async def lifespan(app: FastAPI):
    ExtractService.cleanup_ghost_tasks()
    ScanService.cleanup_ghost_tasks()
    AITaskQueueService()._cleanup_ghost_tasks()
    yield

app = FastAPI(title="Folder Steward", version="0.1.0", lifespan=lifespan)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    finally:
        close_connection()

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
from .api.smart_organize import router as smart_organize_router
from .api.ai_summaries import router as ai_summaries_router
from .api.feedback_rules import router as feedback_rules_router

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
app.include_router(smart_organize_router, prefix="/api")
app.include_router(ai_summaries_router, prefix="/api")
app.include_router(feedback_rules_router, prefix="/api")
