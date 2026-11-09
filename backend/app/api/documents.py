import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.document import DocumentStatus
from app.db.session import get_session
from app.ingestion.parsers.pymupdf_parser import PyMuPDFParser
from app.schemas.document import DocumentDetail, DocumentList, DocumentOut, PageOut, PassageList
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> DocumentService:
    settings = get_settings()
    return DocumentService(session, StorageService(settings.storage_dir, settings.max_upload_bytes), PyMuPDFParser())


Service = Annotated[DocumentService, Depends(get_service)]


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(service: Service, file: UploadFile | None = File(default=None)):
    if file is None:
        raise HTTPException(422, "PDF file is required")
    return await service.upload(file)


@router.get("", response_model=DocumentList)
async def list_documents(service: Service, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: DocumentStatus | None = None):
    items, total = await service.list_documents(page, page_size, status)
    return DocumentList(items=items, total=total, page=page, page_size=page_size)


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(document_id: uuid.UUID, service: Service):
    document = await service.get(document_id)
    return DocumentDetail.model_validate({**DocumentOut.model_validate(document).model_dump(), "passage_count": await service.passage_count(document_id)})


@router.get("/{document_id}/passages", response_model=PassageList)
async def list_passages(document_id: uuid.UUID, service: Service, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100), page_number: int | None = Query(None, ge=1)):
    items, total = await service.passages(document_id, page, page_size, page_number)
    return PassageList(items=items, total=total, page=page, page_size=page_size)


@router.get("/{document_id}/pages/{page_number}", response_model=PageOut)
async def get_page(document_id: uuid.UUID, page_number: int, service: Service):
    if page_number < 1:
        raise HTTPException(422, "Page number must be positive")
    blocks = await service.page(document_id, page_number)
    return PageOut(document_id=document_id, page_number=page_number, blocks=blocks)
