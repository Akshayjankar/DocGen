# Progress

## Phase 1–5 baseline ✅
Core engine, API, frontend, quality harness.

## Revision 2 ✅
WP0–WP5 (dual logos, layout, PreviewSession, Library, polish).

## Revision 3
- **Root cause ✅** — `docs/revision3-rootcause.md` (corner → cover via `_logo_bytes_for` + missing DOCX header logo + single-logo jobs)
- **WP-A ✅** — dual keys, no cover fallback, logos_used, matrix tests
- **WP-B ✅** — hug/margin geometry, CornerPlacementControl, geometry tests
- **WP-E ✅** — Docgen Body, date formats, soft breaks
- **WP-C ✅** — eight format YAMLs, `/api/v1/formats`, suggest, FormatPicker
- **WP-D ✅** — AmbientGlow + OKLCH ambient CSS vars + brandGlow toggle

## Known gaps / deferred
- Full SSIM ≥ 0.99 automated gate for all eight presets
- Playwright ambient hue + axe contrast e2e in CI
- User “Save as my preset” in Brand Kit (P1)
- Anchored `wp:anchor` DOCX hug (table header used; PDF geometry is authoritative)
