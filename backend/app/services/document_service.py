import logging
import uuid

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import DocumentError, DocumentNotFound
from app.db.models.document import Document, DocumentStatus
from app.db.models.source_passage import SourcePassage
from app.ingestion.interfaces import DocumentParser
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self, session: AsyncSession, storage: StorageService, parser: DocumentParser):
        self.session = session
        self.storage = storage
        self.parser = parser

    async def upload(self, file: UploadFile) -> Document:
        stored = await self.storage.save(file)
        document = Document(
            filename=(file.filename or "upload.pdf")[:255],
            storage_key=stored.key,
            content_hash=stored.sha256,
            file_size=stored.size,
            status=DocumentStatus.uploaded,
        )
        try:
            self.session.add(document)
            await self.session.commit()
            await self.session.refresh(document)
        except Exception:
            await self.session.rollback()
            self.storage.delete(stored.key)
            logger.exception("Could not create document record")
            raise

        try:
            document.status = DocumentStatus.processing
            await self.session.commit()
            parsed = await run_in_threadpool(self.parser.parse, stored.path)
            self.session.add_all(
                SourcePassage(
                    document_id=document.id,
                    page_number=block.page_number,
                    block_index=block.block_index,
                    text=block.text,
                    start_char=block.start_char,
                    end_char=block.end_char,
                )
                for block in parsed.blocks
            )
            document.page_count = parsed.page_count
            document.status = DocumentStatus.completed
            document.error_message = None
            await self.session.commit()
            await self.session.refresh(document)
            return document
        except DocumentError as exc:
            await self.session.rollback()
            document.status = DocumentStatus.failed
            document.error_message = exc.message
            await self.session.commit()
            raise DocumentError(f"{exc.message} (document_id: {document.id})", exc.status_code) from exc
        except Exception:
            await self.session.rollback()
            logger.exception("Document processing failed: %s", document.id)
            try:
                document.status = DocumentStatus.failed
                document.error_message = "Document processing failed"
                await self.session.commit()
            except Exception:
                await self.session.rollback()
                logger.exception("Could not persist failed status: %s", document.id)
            raise

    async def get(self, document_id: uuid.UUID) -> Document:
        document = await self.session.get(Document, document_id)
        if document is None:
            raise DocumentNotFound()
        return document

    async def list_documents(self, page: int, page_size: int, status: DocumentStatus | None):
        query = select(Document)
        count = select(func.count()).select_from(Document)
        if status is not None:
            query = query.where(Document.status == status)
            count = count.where(Document.status == status)
        total = await self.session.scalar(count) or 0
        result = await self.session.scalars(query.order_by(Document.created_at.desc(), Document.id.desc()).offset((page - 1) * page_size).limit(page_size))
        return list(result), total

    async def passage_count(self, document_id: uuid.UUID) -> int:
        return await self.session.scalar(select(func.count()).select_from(SourcePassage).where(SourcePassage.document_id == document_id)) or 0

    async def passages(self, document_id: uuid.UUID, page: int, page_size: int, page_number: int | None):
        await self.get(document_id)
        condition = SourcePassage.document_id == document_id
        query = select(SourcePassage).where(condition)
        count = select(func.count()).select_from(SourcePassage).where(condition)
        if page_number is not None:
            query = query.where(SourcePassage.page_number == page_number)
            count = count.where(SourcePassage.page_number == page_number)
        total = await self.session.scalar(count) or 0
        rows = await self.session.scalars(query.order_by(SourcePassage.page_number, SourcePassage.block_index).offset((page - 1) * page_size).limit(page_size))
        return list(rows), total

    async def page(self, document_id: uuid.UUID, page_number: int):
        document = await self.get(document_id)
        if page_number > document.page_count:
            raise DocumentError("Page not found", 404)
        rows = await self.session.scalars(select(SourcePassage).where(SourcePassage.document_id == document_id, SourcePassage.page_number == page_number).order_by(SourcePassage.block_index))
        return list(rows)
