# Revision 2 — Pre-change audit

**Date:** 2026-10-23  
**Scope:** Section 0 of the Revision 2 prompt — map Section 8 paths, reproduce Section 2 findings, **do not start WP0 until this document is accepted**.

**Evidence artifacts:** `tmp_revision2_audit/` (`nwertlif.pdf`, `nwertlif.docx`, `black_box_n.png`, `cover.png`, `page1–4.png`)

---

## 1. Section 8 → real repo mapping

### Backend (`backend/app/`)

| Prompt path / symbol | Real path / status | Notes |
|---|---|---|
| `models/theme.py` (`LogoAsset`, `LogoSet`, `LayoutSpec`, `Theme.logos`) | `models/theme.py` | Exists with `logo_path` / `logo_alt` only — **replace** |
| `models/document.py` (`subtitle`, `doc_id`, `reviewed_by`, `approved_by`) | `models/document.py` | Has `subtitle`, `document_id`, `approver`; **add** `reviewed_by`; align naming |
| `models/db.py` (`BrandKit.logos`, drop `ApiKey`) | `models/db.py` | `BrandKit.logo_path`; `ApiKey` table **exists** |
| `api/v1/logos.py` | — | **Missing** (create) |
| `api/v1/previews.py` | — | **Missing** (create) |
| `api/v1/evals.py` | `api/v1/evals.py` | **Remove** (WP0) |
| API-key auth in `deps.py` | `deps.py` | `ApiKey` lookup helpers — **remove** (WP0) |
| `services/theme_engine/logo.py` | — | **Missing** (create) |
| `services/theme_engine/extract.py` | `services/theme_engine/extract.py` | Exists; extend for processed logos / `palette_source` |
| `services/renderer/cover.py` | `services/renderer/cover.py` | Exists (DOCX cover) |
| `services/renderer/revision.py` | `services/renderer/revision.py` | Exists (DOCX; 5 cols already) |
| `services/renderer/styles.py` | `services/renderer/styles.py` | Exists |
| `services/renderer/oxml.py` | `services/renderer/oxml.py` | Exists |
| `services/renderer/layout.py` | — | **Missing** (create) |
| `services/renderer/header_footer.py` | — | **Missing**; PDF chrome lives in `pdf_native.py` |
| `services/renderer/fonts.py` | — | **Missing**; Arial registration inline in `pdf_native.py` |
| PDF renderer | `services/renderer/pdf.py`, `pdf_native.py`, `pdf_fallback.py` | Native PyMuPDF is primary (`PDF_ENGINE=native`) |
| `services/preview/session.py`, `render_queue.py` | — | **Missing** (WP3) |
| `tests/quality/` | — | **Missing**; evals live under `backend/evals/` + `api/v1/evals.py` |
| Alembic migrations | No app `alembic/` tree yet | **Add** for logo / ApiKey changes |

### Frontend (`frontend/src/`)

| Prompt path | Real path / status |
|---|---|
| Delete `app/evals`, `app/developers` | `app/evals/page.tsx`, `app/developers/page.tsx` — **present** |
| `LogoPair.tsx` / `LogoCard.tsx` / … | — **Missing**; current: `components/studio/LogoDropzone.tsx` |
| `PaperViewer.tsx` / `DraftPaper.tsx` / … | — **Missing**; current: `LivePaperPreview.tsx` (HTML mock, not export-parity) |
| Library components + `lib/library-db.ts` | — **Missing**; current: static `app/library/page.tsx` |
| `hooks/usePreviewSession.ts`, `useLibrary.ts` | — **Missing** |
| `studio/page.tsx`, `studio-store.ts` | Exist — update for dual logos + preview session |
| Header / Footer / CommandPalette | `components/chrome/{Header,Footer,CommandPalette}.tsx` — still link Evals & Developers |
| Custom cursor | `components/chrome/Cursor.tsx` |

### Other

| Item | Status |
|---|---|
| GitHub Action sample | `.github/workflows/ci.yml`, `docgen-markdown.yml` — trim public-eval surface in WP0 |
| OpenAPI `/docs` | Always on via FastAPI default — gate off when `ENV=production` (WP0) |
| `LivePaperPreview` vs export | Preview parses markdown client-side; export uses server blocks/theme — **no shared session** (WP3) |

---

## 2. Finding reproduction (tiny input)

**Input:** title `Nwertlif`, body `Hii I am NEtflic`, logo = red “N” on opaque black 256×256 PNG (`tmp_revision2_audit/black_box_n.png`).  
**Pipeline:** `RulesStructurer` + `extract(logo)` + `render_pdf_from_blocks` / `build_docx`.

| ID | Claim | Reproduced? | Evidence |
|---|---|---|---|
| **F1** | One logo reused; opaque black square | **Yes** | Cover + header both embed same PNG; black box visible on `cover.png` |
| **F2** | Corner logo ~7 mm right of text margin | **Yes** | Logo `x0=93`, `MARGIN_X=72` → **Δ = 7.4 mm** |
| **F3** | Logo ~3 mm from top border; footer cramped | **Partial** | Logo top Δ from border ≈ **3.5 mm** (yes). Footer clearance ≈ **8.1 mm** (meets ≥8 mm already; less severe than “3 mm”) |
| **F4** | Two logos on cover | **Yes** | Cover has **2** image bboxes (corner + center) |
| **F5** | 7 cells under 5 labels + blank rows | **Yes (PDF)** | `pdf_native` draws **7** headers incl. Reviewed/Approved By + **2 blank data rows**. DOCX `revision.py` already uses **5** cols / 1 data row — PDF path is the bug |
| **F6** | Empty Prepared By row | **Yes** | Release Notice includes `Prepared By` with empty value |
| **F7** | Nearly empty pages for 1 sentence | **Yes** | **4 pages** for one body line |
| **F8** | TOC lists itself + front matter | **Yes** | TOC entries: Release Notice, Revision History, Table of Contents, Nwertlif |
| **F9** | Auto H1 = document title | **Yes** | Body page shows heading `Nwertlif` then `Hii I am NEtflic` (`render_blocks` injects title as H1) |
| **F10** | Cover title forced UPPERCASE | **Yes** | Cover shows **`NWERTLIF`**; Release Notice keeps `Nwertlif` |
| **F11** | Soft hyphens in dates | **Yes** | Extracted date `2026\u00ad10\u00ad23` |
| **F12** | Flat typography | **Yes (qualitative)** | Single Arial/Helvetica stack; limited size hierarchy vs Revision 2 scale |
| **F13** | Unrelated color roles | **Yes (code)** | No explicit `brand` / `brand_deep` / `tint` / `ink` / `muted` / `rule` roles table |

### Library (L1–L5)

| ID | Claim | Reproduced? | Evidence |
|---|---|---|---|
| **L1** | Three static samples, not user docs | **Yes** | Hardcoded `samples` in `library/page.tsx` |
| **L2** | Internal env / Phase 2 wording | **Yes** | `STORE_HISTORY=false · FILE_TTL_MINUTES from env`; “When Phase 2 enables…” |
| **L3** | Dashed future placeholder | **Yes** | Bottom dashed panel |
| **L4** | Identical DOC icons; no thumb/download/search/delete | **Yes** | `FileDoc` only; link “Open in Studio →” only |
| **L5** | Custom cursor ring stuck mid-page | **Partial** | `Cursor.tsx` hides on `document.mouseleave` and starts off-screen; ring can remain visible at last coords if leave events are missed — needs WP5 verification in browser |

### Not reproducible / N/A

- None of F1–F13 fully failed to reproduce; F3 footer and L5 are **partial**.
- DOCX revision history does **not** show the 7-column PDF bug (already 5 columns).

---

## 3. Current vs target for the reference input

| Metric | Current | Revision 2 target (#B.4) |
|---|---|---|
| Pages | 4 | **2** |
| TOC | Always (front-matter + title) | None when &lt; 3 body headings |
| Cover logos | Corner + center | Center only (default) |
| Body H1 | Auto title | None if source has no headings |
| Cover title case | UPPERCASE if &lt; 48 chars | As typed |

---

## 4. Gate status

- [x] Path mapping written  
- [x] Findings reproduced (with partial notes)  
- [x] **WP0 complete** — Evals/Developers/ApiKey removed; quality under `tests/quality/`; Alembic drop-apikey. Next: WP1.

---

## 5. Try reproduction yourself

```bash
# PDF/DOCX already at:
open /Users/nseindia/Desktop/Akshay/Projects/DocGen/tmp_revision2_audit/nwertlif.pdf
open /Users/nseindia/Desktop/Akshay/Projects/DocGen/tmp_revision2_audit/cover.png

# Library UI
open http://127.0.0.1:3003/library
```
