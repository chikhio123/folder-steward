from .base import TextExtractor, ExtractResult
from .txt_extractor import TxtExtractor
from .pdf_extractor import PdfExtractor
from .docx_extractor import DocxExtractor

_EXTRACTORS = [TxtExtractor(), PdfExtractor(), DocxExtractor()]

def get_extractor(extension: str) -> TextExtractor | None:
    if not extension:
        return None

    ext = extension.lower()

    for ex in _EXTRACTORS:
        if ext in ex.supported_extensions:
            return ex

    return None
