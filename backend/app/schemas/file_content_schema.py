from pydantic import BaseModel
from typing import Optional

class FileContentResponse(BaseModel):
    file_id: int
    extract_status: str
    text_length: int
    preview: Optional[str] = None
    extracted_at: Optional[str] = None
