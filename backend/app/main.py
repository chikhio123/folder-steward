from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.database import init_db

app = FastAPI(title="Folder Steward", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


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

app.include_router(scan_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(duplicates_router, prefix="/api")
app.include_router(suggestions_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
