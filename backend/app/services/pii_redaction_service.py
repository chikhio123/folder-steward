import re

class PIIRedactionService:
    """Service to redact Personally Identifiable Information (PII) before sending to LLM."""

    # Simplified regex patterns for common PII types
    PATTERNS = {
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "CHINESE_PHONE": r"\b1[3-9]\d{9}\b",
        "CHINESE_ID_CARD": r"\b\d{17}[\dXx]\b",
        "CREDIT_CARD": r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b",
        "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    }

    def __init__(self):
        self._compiled_patterns = {
            name: re.compile(pattern)
            for name, pattern in self.PATTERNS.items()
        }

    def redact(self, text: str) -> str:
        """Redact PII from the given text."""
        if not text:
            return text

        redacted_text = text
        for name, pattern in self._compiled_patterns.items():
            redacted_text = pattern.sub(f"[{name}_REDACTED]", redacted_text)

        return redacted_text

pii_redaction_service = PIIRedactionService()
