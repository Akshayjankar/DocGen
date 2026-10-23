# Docgen

> *Turn rough notes into compliance-grade, on-brand SOPs, setup guides and reports, with your wording untouched.*

Upload **cover + corner logos** + raw notes → get a real branded **Word (.docx)** and **PDF**: cover, release notice, revision history, adaptive TOC, themed headings, striped tables, callouts, code boxes, Page X of Y, page border. Live paper in Studio matches export. Library saves in your browser only.

**New here?** Read the first-time walkthrough: [docs/USER_GUIDE.md](docs/USER_GUIDE.md) (Format vs Improve, logos, Studio, export).

**Demo placeholder:** drop a 60–90s screen recording at `docs/demo.gif` (Chroma Drop → Studio → Export).

## Quick start

```bash
export PATH="$HOME/.local/bin:$PATH"
make setup

# Terminal A — API
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Terminal B — Web
cd frontend && pnpm dev
# → http://localhost:3000
```

### CLI (offline rules structurer)

```bash
cd backend
uv run python -m app.cli build \
  --text ../samples/sop.md \
  --logo ../samples/logo.png \
  --title "Password Reset SOP" \
  --type sop \
  --out ../out \
  --no-pdf
```

### Docker (self-host + Ollama)

```bash
cp .env.example .env
make docker-local   # api + web + ollama profile
```

## Architecture

```
logo → Theme Engine → Theme
text → Ingest → Structurer (LLM|rules) → Block[] → Renderer → DOCX → PDF
                              ↑                         │
                         Verifier ←─────────────────────┘
```

Details: [docs/architecture.md](docs/architecture.md) · [content-lock](docs/content-lock.md) · [API](docs/api.md)

## Quality (CI harness)

Fast matrix (`make eval-fast`, n=6) — internal only; no public UI:

| Metric | Target | Latest |
|---|---|---|
| Content preservation (format-only) | 100% | **100%** |
| WCAG AA pass rate | 100% | **100%** |
| DOCX validity | 100% | **100%** |
| Latency p50 / p95 | tracked | ~91 / ~134 ms |

```bash
make eval-fast   # CI subset
make eval        # full matrix
```

## Before / after

Three brand demos live on the landing page gallery (Acme Blue, Forest, Slate). Left = raw mono notes; right = typeset branded pages.

## Privacy

- No persistent document text by default (`STORE_HISTORY=false`)
- Temp files TTL (default 60 min)
- PII redaction option before cloud LLM calls
- Confidential docs → route to Ollama only
- Free cloud tiers may train on prompts — Studio surfaces a notice

See [/privacy](http://localhost:3000/privacy).

## Health check

```bash
curl -s http://localhost:8000/api/v1/health | jq
curl -s -X POST http://localhost:8000/api/v1/themes/extract \
  -F logo=@samples/logo.png | jq .palette
```

OpenAPI (`/docs`) is available in development only; disabled when `ENV=production`.

## Stack

Backend: Python 3.12, FastAPI, python-docx, coloraide, PyMuPDF (native PDF; LibreOffice optional)  
Frontend: Next.js 16, Tailwind v4, motion, next-themes  
LLM: gemini → groq → openrouter → ollama → **rules fallback** ($0 path)

## License

MIT
