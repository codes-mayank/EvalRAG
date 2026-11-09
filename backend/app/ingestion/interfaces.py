from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ExtractedBlock:
    page_number: int
    block_index: int
    text: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class ParsedDocument:
    page_count: int
    blocks: list[ExtractedBlock]


class DocumentParser(Protocol):
    def parse(self, path: Path) -> ParsedDocument: ...
