# Docgen — Project Brief

## Mission
Build **Docgen**: a full-stack web app that turns a company logo + raw text into compliance-grade, on-brand Word (.docx) and PDF documents.

**Positioning:** *"Turn rough notes into compliance-grade, on-brand SOPs, setup guides and reports, with your wording untouched."*

## Core product loop
1. User uploads logo → Theme Engine extracts brand palette (WCAG AA).
2. User provides text (.txt/.md/.docx or paste) → Ingest normalizes with stable offsets.
3. Structurer (LLM or rules) emits semantic `Block[]` with source spans.
4. Deterministic Renderer builds real DOCX + tagged PDF.
5. Verifier proves content-lock % and document validity.

## Non-negotiables
- LLM never controls layout — only semantic blocks.
- Format-only mode: content-lock 100% by construction (span injection).
- Real Word documents (styles, TOC field, headers/footers, page borders).
- Privacy first; self-host with Ollama; $0 free-tier path.
- Graceful degradation to rules + neutral palette.

## Quality bar
Portfolio flagship targeting 9/10: deterministic renderer, evaluation harness, tests, CI, Docker, distinctive frontend ("Chroma Press").

## Build phases
1. Core engine (backend CLI) — **current**
2. API + LLM structurer
3. Frontend foundation
4. Landing + Studio
5. Proof and polish

See `AGENTS.md` for the full specification.
