from pathlib import Path
from .base import TextExtractor, ExtractResult

class TxtExtractor(TextExtractor):
    supported_extensions = {".txt", ".md", ".csv", ".json"}

    def extract(self, path: Path) -> ExtractResult:
        # 限制最大读取大小，例如 10MB
        MAX_SIZE = 10 * 1024 * 1024

        stat = path.stat()
        if stat.st_size > MAX_SIZE:
            return ExtractResult(
                text="",
                warnings=[f"File too large ({stat.st_size} bytes), skipped."]
            )

        text = ""
        warnings = []
        encodings = ["utf-8", "gbk", "latin-1"]

        raw_bytes = path.read_bytes()
        for enc in encodings:
            try:
                text = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            # 如果都失败了，用 utf-8 强制替换错误字符
            text = raw_bytes.decode("utf-8", errors="replace")
            warnings.append("Decoded with 'utf-8' using replacement for invalid characters.")

        # 截断超长文本 (例如 1,000,000 字符)
        MAX_CHARS = 1_000_000
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]
            warnings.append(f"Text truncated to {MAX_CHARS} characters.")

        return ExtractResult(text=text, warnings=warnings)
