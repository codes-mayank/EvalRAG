import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.document import DocumentStatus


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    filename: str
    content_hash: str
    file_size: int
    page_count: int
    status: DocumentStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentDetail(DocumentOut):
    passage_count: int


class PassageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    page_number: int
    block_index: int
    text: str
    start_char: int
    end_char: int


class DocumentList(BaseModel):
    items: list[DocumentOut]
    total: int
    page: int
    page_size: int


class PassageList(BaseModel):
    items: list[PassageOut]
    total: int
    page: int
    page_size: int


class PageOut(BaseModel):
    document_id: uuid.UUID
    page_number: int = Field(ge=1)
    blocks: list[PassageOut]
