# EvalRAG — Phase 1

Document ingestion foundation for an evaluation-driven RAG platform. This phase stores PDFs, extracts selectable text blocks with page provenance, and provides a small document browser. It does not include chunking, embeddings, search, answer generation, or evaluation.

## Run locally

Requires Python 3.12+ and Node 22+. The default database is a local SQLite file, so no database server is needed.

From the project root, start the API in one terminal:

```sh
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

From the project root, start the frontend in another terminal:

```sh
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000. API docs are at http://localhost:8000/docs. SQLite data is saved in `backend/local.db`; uploaded PDFs are saved in `backend/storage/`.

Run isolated backend tests with `cd backend && .venv/bin/pytest -q`. Tests use a temporary SQLite database and storage directory; they never touch the configured development database.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | API health |
| POST | `/api/v1/documents` | Upload and process a PDF in multipart field `file` |
| GET | `/api/v1/documents` | Paginated list; optional `status` filter |
| GET | `/api/v1/documents/{id}` | Metadata and passage count |
| GET | `/api/v1/documents/{id}/passages` | Paginated blocks; optional `page_number` filter |
| GET | `/api/v1/documents/{id}/pages/{page_number}` | All blocks on one page |

## Architecture notes

- Routes delegate to `DocumentService`; `StorageService` owns bounded file writes and UUID storage keys. Original names are metadata only.
- The parser returns plain structured extraction data, independent of ORM objects. It runs in a threadpool and can be replaced with another `DocumentParser` implementation later.
- Each block is normalized with whitespace collapsed. A page's normalized text is the block texts joined by single spaces, in block order. `start_char` and `end_char` index that exact string, with an exclusive end.
- Upload status is committed as `uploaded`, then `processing`, then `completed` or `failed`. A failed parse remains visible with its error and stored PDF. An initial database insert failure deletes the file. Passage writes and final status share a transaction, so partial passage sets do not commit.
- PDFs with no selectable text receive a failed status and a clear OCR-required error. OCR is outside this phase.
- Migrations own schema creation; the application does not create tables at startup.
