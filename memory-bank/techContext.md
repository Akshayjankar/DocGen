# Tech Context

## Backend
- Python 3.12 via uv
- FastAPI, Pydantic v2, SQLModel, Alembic
- python-docx + lxml for OXML
- Pillow, numpy, scikit-learn, coloraide, cairosvg
- markdown-it-py, rapidfuzz, PyMuPDF
- LibreOffice headless (Docker; may be absent locally)

## Frontend (Phases 3–4)
- Next.js 16, React 19, Tailwind v4, pnpm
- motion, lenis, next-themes, zustand, tanstack-query
- openapi-typescript / openapi-fetch

## Infra
- Docker Compose (api, web, optional ollama)
- GitHub Actions CI
- Makefile targets: setup, dev, test, e2e, lint, eval, types, docker

## Local tooling (this machine)
- uv 0.13.5, Python 3.12.15
- pnpm available (Node 20)
- PDF: native PyMuPDF (`PDF_ENGINE=native`); LibreOffice optional
