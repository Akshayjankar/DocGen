"""Wide tables must keep every cell (no clipped dates / headers)."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from app.models.document import DocumentMeta, RenderOptions
from app.services.ingest.parse import parse_text
from app.services.renderer.pdf_native import render_pdf_from_blocks
from app.services.structurer.rules import RulesStructurer
from app.services.theme_engine.presets import get_preset

SALES = """# Sales

| Order ID | Date | Product | Category | Region | Units Sold | Unit Price | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ORD001 | 2026-01-05 | Laptop | Electronics | West | 2 | 120,000 | 90,000 |
| ORD003 | 2026-01-07 | Desk | Furniture | North | 1 | 25,000 | 18,000 |
| ORD005 | 2026-01-09 | Headphones | Accessories | West | 10 | 8,000 | 5,000 |
"""


def test_wide_table_keeps_dates_and_headers(tmp_path: Path) -> None:
    norm = parse_text(SALES)
    blocks = RulesStructurer().structure(norm, "report", mode="format_only")  # type: ignore[arg-type]
    out = tmp_path / "sales.pdf"
    render_pdf_from_blocks(
        out_path=out,
        source_text=norm.text,
        blocks=blocks,
        theme=get_preset("neutral"),
        meta=DocumentMeta(title="Sales"),
        options=RenderOptions(),
    )
    text = ""
    for page in pymupdf.open(out):
        text += page.get_text()
    flat = text.replace("\u00ad", "").replace("\n", " ")
    assert "Unit" in flat and "Price" in flat
    assert "2026" in flat and "01" in flat and "07" in flat
    assert "Headphones" in flat or "Headphone" in flat
    assert "Accessories" in flat or "Accessorie" in flat
    assert "ORD003" in flat


def test_csv_promotes_to_markdown_table() -> None:
    csv = "Order ID,Date,Product\nORD001,2026-01-05,Laptop\nORD003,2026-01-07,Desk\n"
    norm = parse_text(csv)
    assert "|" in norm.text
    assert "Order ID" in norm.text
    blocks = RulesStructurer().structure(norm, "report", mode="format_only")  # type: ignore[arg-type]
    tables = [b for b in blocks if b.type == "table" and b.table]
    assert tables
    assert tables[0].table.rows[1][1] == "2026-01-07"
