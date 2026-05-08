from pydantic import BaseModel
from typing import Optional, List

class SearchResultItem(BaseModel):
    file_id: int
    filename: str
    current_path: str
    extension: Optional[str] = None
    match_source: str  # "filename" or "content"
    snippet: Optional[str] = None
    score: float = 0.0

class SearchResponse(BaseModel):
    items: List[SearchResultItem]
    total: int

class SearchSuggestionItem(BaseModel):
    type: str  # "filename" or "history"
    text: str
    file_id: Optional[int] = None
    path: Optional[str] = None

class SearchSuggestionResponse(BaseModel):
    items: List[SearchSuggestionItem]
