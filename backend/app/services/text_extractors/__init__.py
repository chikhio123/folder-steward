from .base import TextExtractor, ExtractResult
from .txt_extractor import TxtExtractor

def get_extractor(extension: str) -> TextExtractor | None:
    if not extension:
        return None

    ext = extension.lower()
    extractors = [TxtExtractor()]

    for ex in extractors:
        if ext in ex.supported_extensions:
            return ex

    return None
