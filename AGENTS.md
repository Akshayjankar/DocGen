# DOCGEN — Master Build Prompt for an AI Coding Agent

> Work **phase by phase** (Section 14). Do not start a phase until the previous phase's acceptance checks pass.

---

## 0. MISSION

Build **Docgen** (working name; keep it in one constant `APP_NAME`): a full-stack web application where a user uploads a **company logo** and provides **raw text** (pasted, .txt, .md or .docx). The app extracts a brand theme from the logo, understands the text's structure, and returns a **fully branded, real Word document (.docx) and a matching PDF**: cover page, release notice, revision history, auto table of contents, themed headings, striped tables, callouts, code boxes, header/footer with "Page X of Y", and a themed page border.

**One-line positioning:** *"Turn rough notes into compliance-grade, on-brand SOPs, setup guides and reports, with your wording untouched."*

**Quality bar:** portfolio/resume flagship scoring **9/10 overall**.

---

## 1. NON-NEGOTIABLE PRINCIPLES

1. **The LLM never controls layout.** Semantic blocks only; deterministic renderer applies the theme.
2. **Content-lock guarantee.** Format-only: blocks reference source spans; renderer injects original text. Verifier proves 100%.
3. **Improve mode** may rewrite but must emit per-block diffs for accept/reject.
4. **Real Word documents**: heading styles, TOC field, tables, headers/footers, page-number fields.
5. **Accessible by construction**: WCAG AA, tagged PDF, document language, table header rows, logo alt text.
6. **Privacy first**: no persistent text by default; TTL delete; PII redaction; Ollama self-host; no secrets in frontend.
7. **Graceful degradation**: rules structurer + neutral palette fallbacks.
8. **Everything typed**: Pydantic v2 + TypeScript strict + OpenAPI-generated types.

---

## 2–13. FULL SPEC

See the original master prompt in the repo kickoff message and the detailed module specs under:

- `docs/architecture.md`
- `docs/theme-engine.md`
- `docs/content-lock.md`
- `docs/api.md`
- `docs/limitations.md`
- Stack: Python 3.12 + uv, FastAPI, python-docx, Next.js 16, Tailwind v4, Docker, pnpm
- Env vars: `.env.example`
- Commands: `Makefile`

### Data contracts

Implement exactly as in `backend/app/models/` (`Theme`, `Block`, `SourceSpan`, `DocumentRequest`, …).

### Four-stage pipeline

`Theme Engine → Ingest → Structurer → Renderer` (+ Verifier).

### Build phases (Section 14)

1. **Core engine (backend)** — models, theme, ingest, rules, renderer, PDF, verifier, CLI. Gate: acceptance 1, 3, 5, 8, 9.
2. **API + LLM structurer** — FastAPI, SSE jobs, span-referencing LLM, Improve diffs, brand kits.
3. **Frontend foundation** — Next.js 16, tokens, fonts, light/dark circular reveal, chrome.
4. **Landing + Studio** — Chroma Drop, PaperStack, Studio workspace, Press progress, Content Seal.
5. **Proof and polish** — evals, remaining doc types, Docker local profile, README with real numbers.

**Revision 3** (delta): see `.cursor/rules/revision3.mdc` and `docs/revision3-rootcause.md`. Corner logo never falls back to cover; hug/margin geometry; `templates/formats/*.yaml`; ambient glow; Docgen Body + date formats.

### Agent operating rules

- Never let the LLM produce layout or colors. Never accept free text from the LLM in Format-only.
- Write tests alongside every module. Run `make lint test` before declaring a phase done.
- Prefer content fidelity, accessibility, and determinism. Record decisions in `docs/architecture.md`.
- Do not add features outside this spec until all acceptance criteria pass.
- Report at end of each phase: built / passed / deferred / exact commands.
