from pathlib import Path

import pymupdf

from app.core.exceptions import DocumentError
from app.ingestion.interfaces import ExtractedBlock, ParsedDocument


def normalize_text(text: str) -> str:
    return " ".join(text.split())


class PyMuPDFParser:
    def parse(self, path: Path) -> ParsedDocument:
        try:
            with pymupdf.open(path) as pdf:
                if not pdf.is_pdf:
                    raise DocumentError("Unsupported document format")
                if pdf.needs_pass:
                    raise DocumentError("Encrypted PDFs are not supported")
                if pdf.page_count == 0:
                    raise DocumentError("PDF has no pages")
                blocks: list[ExtractedBlock] = []
                for page_number, page in enumerate(pdf, start=1):
                    offset = 0
                    index = 0
                    for raw in page.get_text("blocks", sort=True):
                        # PyMuPDF block tuple: x0, y0, x1, y1, text, block_no, block_type.
                        if len(raw) > 6 and raw[6] != 0:
                            continue
                        value = normalize_text(raw[4])
                        if not value:
                            continue
                        blocks.append(ExtractedBlock(page_number, index, value, offset, offset + len(value)))
                        offset += len(value) + 1  # normalized page text joins blocks with one space
                        index += 1
                if not blocks:
                    raise DocumentError("No selectable text found; scanned PDFs require OCR")
                return ParsedDocument(pdf.page_count, blocks)
        except DocumentError:
            raise
        except (pymupdf.FileDataError, pymupdf.EmptyFileError, ValueError, RuntimeError) as exc:
            raise DocumentError("Malformed or unsupported PDF") from exc
