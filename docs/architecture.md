# Architecture

## Pipeline

```
logo → Theme Engine → Theme JSON ─────────────────┐
                                                   ▼
text → Ingest → Structurer (LLM|rules) → Block[] → Renderer → DOCX → PDF
         │              │                    ▲         │
         └─ PII         └─ spans/rewrite     └─ Verifier
```

## Principles (locked)

1. **LLM never controls layout.** Semantic blocks only; deterministic renderer owns styles, borders, TOC, headers.
2. **Format-only content-lock.** Blocks cite `SourceSpan` offsets; renderer injects original text. Free text from the LLM is rejected in this mode.
3. **Graceful degradation.** Rules structurer offline; preset palette if logo extraction fails.
4. **Real Word.** Heading styles, TOC field, PAGE/NUMPAGES, `w:pgBorders`, table shading via OXML.

## Phase decisions

### Phase 1
- Structurer = `RulesStructurer` (CLI); PDF via native PyMuPDF (`PDF_ENGINE=native`); LibreOffice optional.
- Content-lock ignores markdown chrome when proving span coverage.

### Phase 2
- FastAPI `/api/v1` with jobs + SSE progress.
- `ProviderRouter`: gemini → groq → openrouter → ollama → (optional paid) → rules.
- Format-only LLM returns segment ids only; unresolved segments auto-appended.
- Improve mode emits per-block word diffs; PATCH accepts/rejects then re-renders.
- Brand kits in SQLite via SQLModel; TTL cleaner on temp job dirs.

### Phase 3–4
- Next.js 16 App Router, Tailwind v4 tokens, Chroma Press UI.
- Studio three-pane; demo press fallback when API offline.

### Phase 5
- `make eval` / `make eval-fast` → `backend/tests/quality/results.{json,md}` (CI only; no public UI)
- CI runs backend tests + fast eval + frontend build
- Example GitHub Action converts Markdown via API
- `docker compose --profile local` includes Ollama

### Revision 3
- Corner logo: `_logo_bytes_for` never falls back to cover `logo_path`; DOCX header embeds corner only; jobs accept `logo_cover`/`logo_corner`.
- Placement: hug (14 mm) / margin (22 mm); aspect-locked.
- Format presets: `app/templates/formats/*.yaml` + `/api/v1/formats`.
- Dates via `LayoutSpec.date_format`; body uses `Docgen Body`.
- Studio dark ambient glow from palette OKLCH (`--amb-1..3`).
- Decisions: `docs/decisions.md`; root cause: `docs/revision3-rootcause.md`.
