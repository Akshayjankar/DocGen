# Decisions log

## Revision 3

- **"Too inside" (N2):** Interpreted as the corner logo floating too far from the page corner (≈35 mm), not too close. Default placement is **Hug corner** (14 mm from page edge); **Align with text** (22 mm) is one click away.
- **"Preset for each format":** One `FormatPreset` YAML per document type under `templates/formats/` (eight built-ins). Brand (logos/colors) stays independent; presets own structure/layout defaults. Section skeletons are live/lint only — never written into exports.
- **F11 soft hyphens:** Retracted. Markers in PDF text extraction inside ordinary words are extraction artifacts, not DOCX corruption. Keep XML free of U+00AD/U+2011 as hygiene only.
- **Corner without cover:** Header has no logo (never silent cover fallback) unless `same_for_both`.
- **Date default:** `LayoutSpec.date_format=human` → `23 Oct 2026`.

## Revision 2 (carry-forward)

- Dual logos: cover centered; corner header-only by default.
- PreviewSession is the single source for live paper and export.
- PDF: native PyMuPDF primary (`PDF_ENGINE=native`).
