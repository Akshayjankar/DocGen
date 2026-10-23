"""Native PDF layout: Jagrook-grade chrome and footer clearance."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pymupdf

from app.models.blocks import Block, SourceSpan
from app.models.document import DocumentMeta
from app.services.renderer.pdf_native import (
    BORDER,
    FOOTER_SAFE_GAP,
    PAGE_H,
    render_pdf_from_blocks,
)
from app.services.theme_engine.presets import get_preset


def _sample_blocks(source: str) -> list[Block]:
    return [
        Block(
            id=uuid4().hex[:12],
            type="heading",
            level=1,
            span=SourceSpan(start=0, end=7),
            origin="source",
        ),
        Block(
            id=uuid4().hex[:12],
            type="paragraph",
            span=SourceSpan(start=9, end=52),
            origin="source",
        ),
        Block(
            id=uuid4().hex[:12],
            type="heading",
            level=2,
            span=SourceSpan(start=54, end=60),
            origin="source",
        ),
        Block(
            id=uuid4().hex[:12],
            type="paragraph",
            span=SourceSpan(start=62, end=len(source)),
            origin="source",
        ),
        Block(
            id=uuid4().hex[:12],
            type="table",
            table=__import__("app.models.blocks", fromlist=["TableData"]).TableData(
                headers=["What", "Address"],
                rows=[
                    ["Maker Portal", "http://localhost:3001"],
                    ["Backend API", "http://localhost:5000"],
                ],
            ),
            origin="source",
        ),
    ]


def test_footer_text_above_bottom_border(tmp_path: Path) -> None:
    source = "# Intro\n\nHello world paragraph that fills a body page.\n\n## More\n\nSecond section."
    out = tmp_path / "native.pdf"
    render_pdf_from_blocks(
        out_path=out,
        source_text=source,
        blocks=_sample_blocks(source),
        theme=get_preset("neutral"),
        meta=DocumentMeta(
            title="Ops Runbook",
            organization="Acme Corp",
            classification="Company Confidential",
            subtitle="Delivered functionality and known limitations",
        ),
    )
    assert out.exists() and out.stat().st_size > 800

    doc = pymupdf.open(out)
    assert doc.page_count >= 2  # cover (+ control) + body
    border_bottom = PAGE_H - BORDER
    # Every page has footer; text must stay above the border
    for i in range(doc.page_count):
        page = doc[i]
        words = page.get_text("words")
        footer_words = [w for w in words if w[3] > border_bottom - 55]
        assert footer_words, f"page {i + 1}: expected footer text"
        max_bottom = max(w[3] for w in footer_words)
        assert max_bottom <= border_bottom - FOOTER_SAFE_GAP + 2.0, (
            f"page {i + 1}: footer overlaps border "
            f"(text_bottom={max_bottom}, border={border_bottom})"
        )
    text0 = doc[0].get_text().replace("\xa0", " ")
    assert "Release Notice" in text0
    assert "Ops Runbook" in text0 or "OPS RUNBOOK" in text0
    doc.close()


def test_ensure_pdf_uses_native_by_default(tmp_path: Path) -> None:
    from docx import Document

    from app.config import get_settings
    from app.services.renderer.pdf import ensure_pdf

    get_settings.cache_clear()
    source = "Hello from native PDF."
    blocks = [
        Block(
            id="a1",
            type="paragraph",
            span=SourceSpan(start=0, end=len(source)),
            origin="source",
        )
    ]
    docx = tmp_path / "doc.docx"
    Document().save(str(docx))

    pdf = ensure_pdf(
        docx,
        out_dir=tmp_path,
        source_text=source,
        blocks=blocks,
        theme=get_preset("neutral"),
        meta=DocumentMeta(title="Native Engine", classification="Internal"),
    )
    assert pdf.exists()
    assert get_settings().pdf_engine == "native"
    opened = pymupdf.open(pdf)
    assert opened.page_count >= 1
    assert "Release Notice" in opened[0].get_text().replace("\xa0", " ")
    opened.close()


def test_pdf_strips_markdown_and_soft_hyphens(tmp_path: Path) -> None:
    """Regression: raw ** markers and soft-hyphen glyph stacking must never appear."""
    from app.models.document import DocType
    from app.services.ingest.parse import parse_text
    from app.services.structurer.rules import RulesStructurer

    src = (
        "# How this works\n\n"
        "How to read this guide. Thir\u00adty-second story with **bold words**.\n\n"
        "| **Project name** | **Guide date** |\n"
        "| --- | --- |\n"
        "| OpsDash | **restaurant chain HQ** |\n\n"
        "Offline air-gap\u00adped installation.\n"
    )
    norm = parse_text(src)
    blocks = RulesStructurer().structure(norm, DocType.sop)
    out = tmp_path / "md.pdf"
    render_pdf_from_blocks(
        out_path=out,
        source_text=norm.text,
        blocks=blocks,
        theme=get_preset("neutral"),
        meta=DocumentMeta(title="OpsDash", classification="INTERNAL"),
    )
    doc = pymupdf.open(out)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    assert "**" not in text, text
    # Soft hyphens cause stacked/overlapping glyphs in Preview — must be absent
    assert "\u00ad" not in text, repr(text)
    assert "Project name" in text
    assert "restaurant chain HQ" in text
    assert "Thirty-second" in text
    assert "bold words" in text
    assert "air-gapped" in text
