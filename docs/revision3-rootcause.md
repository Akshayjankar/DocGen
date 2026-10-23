# Revision 3 — Root cause: header shows cover logo (N1)

**Date:** 2026-10-23  
**Method:** Distinct fixtures A (blue 128²) and B (red 128²), SHA-256 logged at each layer; code inspection of Studio → `/previews` → `LogoSet` → `pdf_native._logo_bytes_for` → PDF images.

## Evidence (repro script)

| Layer | Cover SHA-256 (prefix) | Corner SHA-256 (prefix) | Notes |
|---|---|---|---|
| (a) Fixture bytes | `258ee18b2a3a…` | `a77b55217243…` | Distinct |
| (b) After `process_logo` | `673fbb568941…` | `434ecb26275e…` | Distinct processed PNGs |
| (c) `_logo_bytes_for` with both assets on `LogoSet` | cover=`673f…` | corner=`434e…` | Correct when paths resolve |
| (d) `_logo_bytes_for(theme, "corner")` with `logos.corner=None` but `theme.logo_path=cover` | — | **returns cover bytes** | **First layer where B → A** |
| (e) DOCX `word/header*.xml` | — | **no image relationship** | Header builder never embeds a logo |

Commands (from repo):

```bash
cd backend && .venv/bin/python  # see /tmp/docgen_r3_repro from agent session
```

## Causes (verified)

### Cause 1 — Primary (renderer fallback) — **N1**

**File:** `backend/app/services/renderer/pdf_native.py` — `_logo_bytes_for`  
After failing to read `logos.corner`, the function falls through to:

```python
if theme.logo_path and Path(theme.logo_path).exists():
    return Path(theme.logo_path).read_bytes()  # always COVER
```

So any missing/unreadable corner asset silently becomes the cover logo in the header.

**Fix (one sentence):** Return `fallback` only for the requested role; never use `logo_path` when resolving `corner` unless `same_for_both`.

**Guard test:** `tests/unit/test_logo_matrix.py` — corner missing must yield `None` header logo, not cover bytes.

### Cause 2 — DOCX header has no corner slot — **N1 (DOCX)**

**File:** `backend/app/services/renderer/docx_builder.py` — `_setup_header_footer` (~L108–123)  
Header is title + classification text only; no picture from `logos.corner`.

**Fix:** Build header as a 2-column table (or anchored picture) using **only** `logos.corner` (or cover when `same_for_both`).

**Guard test:** DOCX matrix — `header*.xml.rels` Target media hash equals corner processed hash when A≠B.

### Cause 3 — Preview/session passes only cover bytes — **N1 (latent)**

**File:** `backend/app/api/v1/previews.py` — `_build_session` / `create_preview`  
`ensure_pdf(..., logo_bytes=logo_bytes)` passes **cover** only. Corner depends entirely on `theme.logos.corner.processed_path`. Combined with Cause 1, any path miss → cover in header.

**Fix:** Pass explicit `cover_bytes` and `corner_bytes` into the renderer; include both SHA-256 in the preview cache key and `logos_used` response.

### Cause 4 — Documents job API is single-logo — **N1 (export via Run press)**

**File:** `backend/app/api/v1/documents.py` — single `logo` upload; `job_runner` never receives a corner file.

**Fix:** Accept `logo_cover` / `logo_corner` (keep `logo` as cover alias) and persist both on `Theme.logos`.

### Ruled out

| Hypothesis | Result |
|---|---|
| Frontend shared FormData key `logo` for both | **No** — `api.ts` sends `logo` + `corner_logo` |
| `same_for_both` default true | **No** — defaults `False` in model + store |
| Alembic mirroring cover→corner | **No** — no such migration |
| Preview cache ignoring logo hashes | **Partial** — in-memory sessions rebuild each time; no content-hash cache yet (add in WP-A anyway) |

## Placement findings (N2/N3) — for WP-B

**File:** `pdf_native.py` `_insert_logo` + `_draw_header`  
Logo placed in a **38×11 mm** box at `x=MARGIN_X` (22 mm) with `keep_proportion=True`. PyMuPDF **centers** a square mark inside that wide box → left edge ≈ 22 + (38−11)/2 ≈ **35.5 mm** (matches audit “35 mm from page edge”). Aspect look “stretched” if the fitted bbox is misread; true fix: left/right-align within a height-locked box and set `cx/cy` from asset aspect.

## Report summary

| Item | Value |
|---|---|
| **Cause** | Corner resolver falls back to cover `logo_path`; DOCX header never uses corner; session/job APIs under-specify corner bytes |
| **File:line** | `pdf_native.py` `_logo_bytes_for` fallback; `docx_builder.py` `_setup_header_footer`; `previews.py` / `documents.py` |
| **Fix** | Role-strict resolution + real header corner embed + dual-logo request + `logos_used` |
| **Test** | Four-case logo matrix on DOCX media + PDF `get_images` / perceptual hash |
