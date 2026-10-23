# Active Context

## Current focus
**Revision 3** — corner logo root-cause fixed; WP-A/B/E/C/D implemented end-to-end.

## Recent changes (Rev3)
- Root cause: `pdf_native._logo_bytes_for` fell back to cover `logo_path` for corner → `docs/revision3-rootcause.md`
- Dual FormData keys `logo_cover`/`logo_corner`; documents + job_runner process both; header uses corner only
- Geometry: hug 14 mm / margin 22 mm; aspect-locked edge-aligned placement
- Eight `templates/formats/*.yaml` + `/api/v1/formats`; suggest + apply helpers
- Dates: `LayoutSpec.date_format` (default human `23 Oct 2026`); Docgen Body style
- FE: AmbientGlow, CornerPlacementControl, FormatPicker, brandGlow, OKLCH ambient vars

## Next steps
- Optional: full SSIM preview-vs-export gate; Playwright ambient hue e2e; user custom presets in Brand Kit
- Visual QA with Capgemini-style A/B logos

## Active decisions
See `docs/decisions.md` (Rev3 interpretation notes).
Preview and export share one session; LLM never owns layout/logos.
