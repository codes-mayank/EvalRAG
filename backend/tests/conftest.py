import os
from collections.abc import AsyncIterator

import pymupdf
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.db import models as _models  # noqa: F401


@pytest.fixture
def pdf_bytes():
    def make(pages: list[list[str]]) -> bytes:
        pdf = pymupdf.open()
        for lines in pages:
            page = pdf.new_page()
            for index, line in enumerate(lines):
                page.insert_text((72, 72 + index * 72), line)
        data = pdf.tobytes()
        pdf.close()
        return data
    return make


@pytest.fixture
async def client(tmp_path, monkeypatch) -> AsyncIterator[AsyncClient]:
    from app.core.config import get_settings
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    get_settings.cache_clear()
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def session_override():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()
    get_settings.cache_clear()
    await engine.dispose()
