import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import DocumentError

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="EvalRAG API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(DocumentError)
async def document_error_handler(request: Request, exc: DocumentError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(health_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
