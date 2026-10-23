# Theme Engine

## Pipeline

1. Load logo (SVG via cairosvg → PNG; raster downscale ≤256px).
2. Drop transparent / near-white / near-black edge-dominant pixels.
3. k-means (k=6) in CIELAB; merge ΔE < 12; rank by population × chroma.
4. `primary` / `secondary` / `accent` selection; complementary if monochrome.
5. `derive.py` builds tint/dark + semantic callout hues ≥ 40° from primary.
6. `contrast.py` enforces WCAG AA; records adjustments.
7. Low confidence → `presets.py` (`source="preset"`).

## Fonts

Restricted to Word + Docker-shipped faces: Carlito, Liberation Sans/Serif/Mono, mood-keyed pairs.
