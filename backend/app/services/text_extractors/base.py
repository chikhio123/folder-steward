from dataclasses import dataclass, field
from pathlib import Path
from typing import Set

@dataclass
class ExtractResult:
    text: str
    metadata: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

class TextExtractor:
    supported_extensions: Set[str] = set()

    def extract(self, path: Path) -> ExtractResult:
        raise NotImplementedError
