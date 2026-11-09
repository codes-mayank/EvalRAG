import re
import sqlite3

import pymupdf
import pytest

from app.ingestion.parsers.pymupdf_parser import PyMuPDFParser


async def upload(client, data, name="test.pdf"):
    return await client.post("/api/v1/documents", files={"file": (name, data, "application/pdf")})


@pytest.mark.asyncio
async def test_success_retrieval_and_offsets(client, pdf_bytes):
    response = await upload(client, pdf_bytes([["First block", "Second block"], ["Page two"]]))
    assert response.status_code == 201, response.text
    document = response.json()
    assert document["status"] == "completed"
    assert document["page_count"] == 2
    assert re.fullmatch(r"[0-9a-f]{64}", document["content_hash"])
    document_id = document["id"]
    detail = (await client.get(f"/api/v1/documents/{document_id}")).json()
    assert detail["passage_count"] == 3
    listing = (await client.get("/api/v1/documents?status=completed&page_size=1")).json()
    assert listing["total"] == 1
    passages = (await client.get(f"/api/v1/documents/{document_id}/passages?page_number=1")).json()
    assert passages["total"] == 2
    blocks = (await client.get(f"/api/v1/documents/{document_id}/pages/1")).json()["blocks"]
    normalized_page = " ".join(block["text"] for block in blocks)
    for block in blocks:
        assert normalized_page[block["start_char"]:block["end_char"]] == block["text"]
    assert [block["page_number"] for block in blocks] == [1, 1]
    assert (await client.get(f"/api/v1/documents/{document_id}/pages/2")).json()["blocks"][0]["page_number"] == 2
    assert (await client.get(f"/api/v1/documents/{document_id}/pages/3")).status_code == 404


@pytest.mark.asyncio
async def test_invalid_and_size_limit(client, monkeypatch, tmp_path):
    assert (await upload(client, b"hello", "fake.pdf")).status_code == 422
    assert (await upload(client, b"%PDF-not-real")).status_code == 422
    assert (await client.post("/api/v1/documents")).status_code == 422
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "10")
    from app.core.config import get_settings
    get_settings.cache_clear()
    assert (await upload(client, b"%PDF-" + b"x" * 20)).status_code == 413
    # Malformed PDFs are retained as failed documents; oversized and non-PDF files are removed.
    assert len(list((tmp_path / "storage").glob("*.pdf"))) == 1


@pytest.mark.asyncio
async def test_empty_text_is_failed(client, pdf_bytes):
    response = await upload(client, pdf_bytes([[], []]))
    assert response.status_code == 422
    assert "No selectable text" in response.json()["detail"]
    listing = (await client.get("/api/v1/documents?status=failed")).json()
    assert listing["total"] == 1
    assert "No selectable text" in listing["items"][0]["error_message"]


@pytest.mark.asyncio
async def test_encrypted_pdf_is_rejected(client):
    pdf = pymupdf.open()
    pdf.new_page().insert_text((72, 72), "Secret")
    data = pdf.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="secret")
    pdf.close()
    response = await upload(client, data)
    assert response.status_code == 422
    assert "Encrypted" in response.json()["detail"]


@pytest.mark.asyncio
async def test_processing_status_is_persisted_before_parsing(client, pdf_bytes, tmp_path, monkeypatch):
    original = PyMuPDFParser.parse
    statuses = []

    def inspect_status(self, path):
        with sqlite3.connect(tmp_path / "test.db") as connection:
            statuses.extend(row[0] for row in connection.execute("SELECT status FROM documents"))
        return original(self, path)

    monkeypatch.setattr(PyMuPDFParser, "parse", inspect_status)
    response = await upload(client, pdf_bytes([["Text"]]))
    assert response.status_code == 201
    assert statuses == ["processing"]
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_page_without_text_in_partially_textual_pdf(client, pdf_bytes):
    response = await upload(client, pdf_bytes([["Page one"], [], ["Page three"]]))
    assert response.status_code == 201
    assert response.json()["page_count"] == 3
    document_id = response.json()["id"]
    blank_page = await client.get(f"/api/v1/documents/{document_id}/pages/2")
    assert blank_page.status_code == 200
    assert blank_page.json()["blocks"] == []


@pytest.mark.asyncio
async def test_not_found(client):
    assert (await client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000")).status_code == 404


@pytest.mark.asyncio
async def test_initial_commit_failure_cleans_file(client, pdf_bytes, tmp_path, monkeypatch):
    from app.api.documents import get_service
    from app.core.config import get_settings
    from app.services.document_service import DocumentService
    from app.services.storage_service import StorageService
    from app.main import app

    class FailingSession:
        def add(self, value):
            pass
        async def commit(self):
            raise RuntimeError("database unavailable")
        async def rollback(self):
            pass

    app.dependency_overrides[get_service] = lambda: DocumentService(FailingSession(), StorageService(get_settings().storage_dir, get_settings().max_upload_bytes), PyMuPDFParser())
    try:
        with pytest.raises(RuntimeError):
            await upload(client, pdf_bytes([["text"]]))
        assert not list((tmp_path / "storage").glob("*.pdf"))
    finally:
        app.dependency_overrides.pop(get_service, None)
