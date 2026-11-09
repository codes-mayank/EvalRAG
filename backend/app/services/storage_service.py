import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import DocumentError


@dataclass(frozen=True)
class StoredFile:
    key: str
    path: Path
    size: int
    sha256: str


class StorageService:
    def __init__(self, directory: Path, max_bytes: int):
        self.directory = directory
        self.max_bytes = max_bytes

    async def save(self, upload: UploadFile) -> StoredFile:
        self.directory.mkdir(parents=True, exist_ok=True)
        key = f"{uuid.uuid4()}.pdf"
        path = self.directory / key
        digest = hashlib.sha256()
        size = 0
        header = b""
        try:
            with path.open("xb") as target:
                while chunk := await upload.read(1024 * 1024):
                    if not header:
                        header = chunk[:5]
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise DocumentError(f"PDF exceeds the {self.max_bytes} byte size limit", 413)
                    digest.update(chunk)
                    target.write(chunk)
            if not size:
                raise DocumentError("PDF is empty")
            if header != b"%PDF-":
                raise DocumentError("File is not a PDF")
            return StoredFile(key, path, size, digest.hexdigest())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

    def delete(self, key: str) -> None:
        (self.directory / key).unlink(missing_ok=True)
