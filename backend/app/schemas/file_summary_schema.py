from pydantic import BaseModel
from typing import Optional

class GenerateSummaryRequest(BaseModel):
    file_id: int

class FileSummaryResponse(BaseModel):
    file_id: int
    summary: str
    status: str
    error_message: Optional[str] = None
