from pathlib import Path
from pypdf import PdfReader
from pypdf.errors import PyPdfError, FileNotDecryptedError
from .base import TextExtractor, ExtractResult

class PdfExtractor(TextExtractor):
    supported_extensions = {".pdf"}

    def extract(self, path: Path) -> ExtractResult:
        # 限制最大读取大小，例如 50MB
        MAX_SIZE = 50 * 1024 * 1024
        MAX_PAGES = 300
        MAX_CHARS = 1_000_000

        stat = path.stat()
        if stat.st_size > MAX_SIZE:
            return ExtractResult(
                text="",
                warnings=[f"File too large ({stat.st_size} bytes), skipped."]
            )

        text_blocks = []
        warnings = []
        metadata = {}

        try:
            reader = PdfReader(str(path))

            if reader.is_encrypted:
                return ExtractResult(
                    text="",
                    warnings=["PDF is encrypted, skipped."]
                )

            num_pages = len(reader.pages)
            metadata["total_pages"] = num_pages

            pages_to_process = min(num_pages, MAX_PAGES)
            if num_pages > MAX_PAGES:
                warnings.append(f"PDF has {num_pages} pages, only extracted first {MAX_PAGES}.")

            for i in range(pages_to_process):
                page = reader.pages[i]
                page_text = page.extract_text()
                if page_text:
                    text_blocks.append(page_text.strip())

            full_text = "\n\n".join(text_blocks).strip()

            if not full_text:
                return ExtractResult(
                    text="",
                    warnings=["no_extractable_text"]
                )

            if len(full_text) > MAX_CHARS:
                full_text = full_text[:MAX_CHARS]
                warnings.append(f"Text truncated to {MAX_CHARS} characters.")

            return ExtractResult(text=full_text, metadata=metadata, warnings=warnings)

        except FileNotDecryptedError:
            return ExtractResult(text="", warnings=["PDF is encrypted or requires password, skipped."])
        except PyPdfError as e:
            return ExtractResult(text="", warnings=[f"PDF parsing error: {e}"])
        except Exception as e:
            return ExtractResult(text="", warnings=[f"Unexpected error reading PDF: {e}"])
