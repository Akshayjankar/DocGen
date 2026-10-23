# System Patterns

## Four-stage pipeline
```
logo → Theme Engine → Theme
text → Ingest → Structurer → Block[] → Renderer → DOCX → PDF
                              ↑              ↓
                         Verifier ←──────────┘
```

## Key decisions
1. **Deterministic renderer** owns all layout; LLM emits semantic blocks only.
2. **Span-referencing** in Format-only: blocks cite source offsets; renderer injects original text.
3. **Provider router** with RPM/RPD limits, 429/5xx rotation, rules fallback last.
4. **Jobs + SSE** for progress; temp storage with TTL.
5. **Two-pass TOC**: DOCX → PDF → extract page numbers → rebuild cached TOC → final PDF.

## Module boundaries
- `theme_engine/` — palette/fonts/border only
- `ingest/` — normalize + PII
- `structurer/` — Block[] production
- `renderer/` — DOCX/PDF only
- `verifier/` — scores and lint, no mutation

## Doc types (Phase 1)
SOP, report, setup_guide — YAML templates define required sections and cover defaults.
