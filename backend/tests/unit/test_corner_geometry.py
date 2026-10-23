"""Revision 3 WP-B: corner logo geometry (hug vs margin)."""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from app.models.document import DocumentMeta, RenderOptions
from app.models.theme import LogoRole, LogoSet
from app.services.ingest.parse import parse_text
from app.services.renderer.pdf_native import render_pdf_from_blocks
from app.services.structurer.rules import RulesStructurer
from app.services.theme_engine.extract import extract
from app.services.theme_engine.logo import process_logo

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "logos"
BLUE = FIXTURES / "blue_drop.png"
RED = FIXTURES / "red_n_black_box.png"

BODY = """# Purpose

Body text for geometry.

# Scope

More body so we get a second page with a header logo.

# Procedure

1. Step one with enough prose to force pagination past the cover.
2. Step two continues the story so the PDF renderer emits a body page.
3. Step three adds yet more content for a reliable page-2 header sample.
"""


def _pt_to_mm(pt: float) -> float:
    return pt * 25.4 / 72.0


@pytest.mark.parametrize("anchor,edge_mm", [("corner", 14.0), ("margin", 22.0)])
@pytest.mark.parametrize("position", ["left", "right"])
def test_corner_logo_edge(tmp_path: Path, anchor: str, edge_mm: float, position: str) -> None:
    cover = BLUE.read_bytes()
    corner = RED.read_bytes()
    theme = extract(cover, name="Geo")
    cover_a, _ = process_logo(cover, role=LogoRole.cover, out_dir=tmp_path)
    corner_a, _ = process_logo(corner, role=LogoRole.corner, out_dir=tmp_path)
    theme.logos = LogoSet(
        cover=cover_a,
        corner=corner_a,
        same_for_both=False,
        corner_anchor=anchor,  # type: ignore[arg-type]
        corner_position=position,  # type: ignore[arg-type]
        corner_pages="all_except_cover",
        corner_height_mm=11.0,
    )
    theme.logo_path = cover_a.processed_path

    normalized = parse_text(BODY * 3)
    blocks = RulesStructurer().structure(normalized, "sop", mode="format_only")  # type: ignore[arg-type]
    meta = DocumentMeta(title="Geometry", date="2026-10-23", classification="Internal")
    out = tmp_path / f"geo_{anchor}_{position}.pdf"
    render_pdf_from_blocks(
        out_path=out,
        source_text=normalized.text,
        blocks=blocks,
        theme=theme,
        meta=meta,
        options=RenderOptions(),
        logo_bytes=cover,
        corner_bytes=corner,
    )
    doc = pymupdf.open(out)
    assert doc.page_count >= 2
    # Cover (page 0) should not have corner by default
    # Body page header logo
    page = doc[1]
    infos = page.get_image_info()
    assert infos, "body page must show corner logo"
    # Pick the topmost image as header logo
    info = min(infos, key=lambda im: im["bbox"][1])
    x0, y0, x1, y1 = info["bbox"]
    page_w = page.rect.width
    if position == "left":
        edge = _pt_to_mm(x0)
        assert abs(edge - edge_mm) <= 0.8, f"left edge {edge:.2f}mm vs {edge_mm}"
    else:
        edge = _pt_to_mm(page_w - x1)
        assert abs(edge - edge_mm) <= 0.8, f"right edge {edge:.2f}mm vs {edge_mm}"
    top = _pt_to_mm(y0)
    assert abs(top - 14.0) <= 0.8, f"top {top:.2f}mm"
    # Aspect within ~5% (processed may trim)
    bw = x1 - x0
    bh = y1 - y0
    assert bh > 0
    aspect = bw / bh
    assert abs(aspect - (corner_a.aspect or 1.0)) / max(corner_a.aspect or 1.0, 0.01) <= 0.05
    # Clearance from border (20pt ≈ 7mm) ≥ 5mm → edge ≥ ~12mm for hug; we already check 14
    border_mm = _pt_to_mm(20.0)
    clear = edge - border_mm if position == "left" else edge - border_mm
    assert clear >= 4.5
    doc.close()
