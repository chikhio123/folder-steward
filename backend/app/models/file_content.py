from dataclasses import dataclass
from typing import Optional

@dataclass
class FileContent:
    id: Optional[int] = None
    file_id: int = 0
    text_content: Optional[str] = None
    text_length: int = 0
    extractor_type: str = ""
    extract_status: str = "pending"
    error_message: Optional[str] = None
    extracted_at: Optional[str] = None
    updated_at: Optional[str] = None
