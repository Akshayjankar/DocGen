# API

Phase 2 will expose `/api/v1` endpoints documented in OpenAPI via FastAPI.

| Method | Path | Purpose |
|---|---|---|
| POST | `/themes/extract` | logo/docx → Theme |
| POST | `/documents` | create job |
| GET | `/jobs/{id}` / `/jobs/{id}/events` | status / SSE |
| GET | `/documents/{id}/download` | docx\|pdf |
| CRUD | `/brand-kits` | saved themes |
| GET | `/health` | liveness |

Phase 1 entry point: `python -m app.cli build`.
